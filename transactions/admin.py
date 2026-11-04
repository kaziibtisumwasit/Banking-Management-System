from django.contrib import admin
from .models import Transaction
from .views import transaction_email


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = [
        "account",
        "amount",
        "balance_after_transaction",
        "transaction_type",
        "loan_approve",
        "time_stamp",
    ]

    def save_model(self, request, obj, form, change):
        if obj.loan_approve and ("loan_approve" in form.changed_data):
            obj.account.balance += obj.amount
            obj.balance_after_transaction = obj.account.balance
            obj.account.save(update_fields=["balance"])

            transaction_email(
                user=obj.account.user,
                email_subject="Loan Approved Confirmation",
                amount=obj.amount,
                balance=obj.account.balance,
                template_name="transactions/loan_approved_confirmation_email.html",
            )
        super().save_model(request, obj, form, change)
