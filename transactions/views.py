from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView, ListView, View, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction as db_transaction
from django.db.models import Sum
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from accounts.models import UserBankAccount
from .models import Transaction
from .forms import DepositForm, LoanRequestForm, WithdrawForm, TransferForm
from .constance import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID, MONEY_SEND, MONEY_RECEIVED


def transaction_email(user, email_subject, amount, balance, template_name, sender=None, receiver=None):
    if not user or not user.email:
        return
    try:
        message = render_to_string(
            template_name,
            {
                "user": user,
                "amount": amount,
                "balance": balance,
                "sender": sender,
                "receiver": receiver,
            },
        )
        send_email = EmailMultiAlternatives(email_subject, "", to=[user.email])
        send_email.attach_alternative(message, "text/html")
        send_email.send()
    except Exception:
        pass


class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = "transactions/transaction_form.html"
    model = Transaction
    title = "Transaction"
    success_url = reverse_lazy("transaction_report")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({"account": self.request.user.account})
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({"title": self.title})
        return context


class DepositeMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = "Deposit Money"

    def get_initial(self):
        return {"transaction_type": DEPOSIT}

    def form_valid(self, form):
        amount = form.cleaned_data.get("amount")
        account = self.request.user.account
        account.balance += amount
        account.save(update_fields=["balance"])

        messages.success(
            self.request,
            f"${amount:,.2f} was deposited into your account successfully!",
        )
        transaction_email(
            self.request.user,
            "Deposit Confirmation",
            amount,
            account.balance,
            "transactions/deposit_confirmation_email.html",
        )
        return super().form_valid(form)


class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = "Withdraw Money"

    def get_initial(self):
        return {"transaction_type": WITHDRAWAL}

    def form_valid(self, form):
        amount = form.cleaned_data.get("amount")
        account = self.request.user.account
        account.balance -= amount
        account.save(update_fields=["balance"])

        messages.success(self.request, f"${amount:,.2f} withdrawn successfully!")
        transaction_email(
            self.request.user,
            "Withdraw Confirmation",
            amount,
            account.balance,
            "transactions/withdraw_confirmation_email.html",
        )
        return super().form_valid(form)


class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = "Request For Loan"

    def get_initial(self):
        return {"transaction_type": LOAN}

    def form_valid(self, form):
        amount = form.cleaned_data.get("amount")
        account = self.request.user.account
        current_loan_count = Transaction.objects.filter(
            account=account, transaction_type=LOAN, loan_approve=True
        ).count()

        if current_loan_count >= 3:
            messages.error(
                self.request,
                "You have reached the maximum limit of 3 active approved loans.",
            )
            return redirect("loan_list")

        messages.success(
            self.request,
            f"Loan request for ${amount:,.2f} has been submitted for admin approval.",
        )
        transaction_email(
            self.request.user,
            "Loan Request Confirmation",
            amount,
            account.balance,
            "transactions/loan_request_confirmation_email.html",
        )
        return super().form_valid(form)


class TransactionRepostView(LoginRequiredMixin, ListView):
    template_name = "transactions/transaction_report.html"
    model = Transaction
    balance = 0
    title = "Transaction Report"

    def get_queryset(self):
        queryset = super().get_queryset().filter(account=self.request.user.account)
        start_date_str = self.request.GET.get("start_date")
        end_date_str = self.request.GET.get("end_date")

        if start_date_str and end_date_str:
            try:
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
                queryset = queryset.filter(
                    time_stamp__date__gte=start_date,
                    time_stamp__date__lte=end_date,
                )
                self.balance = (
                    queryset.aggregate(Sum("amount"))["amount__sum"]
                    or 0
                )
            except ValueError:
                self.balance = self.request.user.account.balance
        else:
            self.balance = self.request.user.account.balance

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "account": self.request.user.account,
                "title": self.title,
                "filtered_balance": self.balance,
                "start_date": self.request.GET.get("start_date", ""),
                "end_date": self.request.GET.get("end_date", ""),
            }
        )
        return context


class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(
            Transaction, id=loan_id, account=request.user.account
        )
        if loan.loan_approve:
            user_account = loan.account
            if loan.amount <= user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save(update_fields=["balance"])
                loan.transaction_type = LOAN_PAID
                loan.save()

                transaction_email(
                    user=loan.account.user,
                    email_subject="Loan Paid Confirmation",
                    amount=loan.amount,
                    balance=loan.balance_after_transaction,
                    template_name="transactions/loan_paid_confirmation_email.html",
                )
                messages.success(
                    request, f"Loan amount ${loan.amount:,.2f} paid successfully!"
                )
                return redirect("transaction_report")
            else:
                messages.error(
                    request,
                    "Your available balance is insufficient to repay this loan.",
                )
                return redirect("loan_list")
        messages.warning(request, "This loan has not been approved yet.")
        return redirect("loan_list")


class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/loan_request.html"
    context_object_name = "loans"

    def get_queryset(self):
        return Transaction.objects.filter(
            account=self.request.user.account, transaction_type=LOAN
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Loan Management"
        return context


class TransferMoneyView(LoginRequiredMixin, FormView):
    template_name = "transactions/transaction_form.html"
    form_class = TransferForm
    success_url = reverse_lazy("transaction_report")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["account"] = self.request.user.account
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Transfer Money"
        return context

    def form_valid(self, form):
        receiver_account_number = form.cleaned_data["account_number"]
        amount = form.cleaned_data["amount"]
        sender = self.request.user.account
        receiver = UserBankAccount.objects.filter(
            account_no=receiver_account_number
        ).first()

        if not receiver:
            form.add_error("account_number", "Receiver account was not found.")
            return self.form_invalid(form)

        with db_transaction.atomic():
            sender.balance -= amount
            sender.save(update_fields=["balance"])

            receiver.balance += amount
            receiver.save(update_fields=["balance"])

            Transaction.objects.create(
                account=sender,
                amount=amount,
                transaction_type=MONEY_SEND,
                balance_after_transaction=sender.balance,
            )

            Transaction.objects.create(
                account=receiver,
                amount=amount,
                transaction_type=MONEY_RECEIVED,
                balance_after_transaction=receiver.balance,
            )

        messages.success(
            self.request,
            f"${amount:,.2f} transferred successfully to Account #{receiver.account_no}.",
        )
        transaction_email(
            user=sender.user,
            email_subject="Money Transfer Confirmation",
            amount=amount,
            balance=sender.balance,
            template_name="transactions/money_transfer_sender_confirmation_email.html",
            sender=sender,
            receiver=receiver,
        )
        transaction_email(
            user=receiver.user,
            email_subject="Money Received Confirmation",
            amount=amount,
            balance=receiver.balance,
            template_name="transactions/money_received_confirmation_email.html",
            sender=sender,
            receiver=receiver,
        )
        return super().form_valid(form)
