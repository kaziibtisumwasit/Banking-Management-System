from django import forms
from accounts.models import UserBankAccount
from .models import Transaction


class TransactionForms(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["amount", "transaction_type"]

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)
        self.fields["transaction_type"].disabled = True
        self.fields["transaction_type"].widget = forms.HiddenInput()

    def save(self, commit=True):
        self.instance.account = self.account
        self.instance.balance_after_transaction = self.account.balance
        return super().save(commit=commit)


class DepositForm(TransactionForms):
    def clean_amount(self):
        min_deposit_amount = 100
        amount = self.cleaned_data.get("amount")
        if amount is None or amount < min_deposit_amount:
            raise forms.ValidationError(
                f"You need to deposit at least ${min_deposit_amount}."
            )
        return amount


class WithdrawForm(TransactionForms):
    def clean_amount(self):
        account = self.account
        min_withdraw = 500
        max_withdraw = 20000
        balance = account.balance
        amount = self.cleaned_data.get("amount")

        if amount is None or amount < min_withdraw:
            raise forms.ValidationError(
                f"You can withdraw at least ${min_withdraw}."
            )
        if amount > max_withdraw:
            raise forms.ValidationError(
                f"You can withdraw at most ${max_withdraw} per transaction."
            )
        if amount > balance:
            raise forms.ValidationError(
                f"You have ${balance} in your account. You cannot withdraw more than your available balance."
            )
        return amount


class LoanRequestForm(TransactionForms):
    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None or amount <= 0:
            raise forms.ValidationError("Please enter a valid positive loan amount.")
        return amount


class TransferForm(forms.Form):
    account_number = forms.IntegerField(label="Receiver Account Number")
    amount = forms.DecimalField(max_digits=12, decimal_places=2, min_value=1)

    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop("account", None)
        super().__init__(*args, **kwargs)

    def clean_account_number(self):
        acc_no = self.cleaned_data.get("account_number")
        if self.account and acc_no == self.account.account_no:
            raise forms.ValidationError("You cannot transfer money to your own account.")
        if not UserBankAccount.objects.filter(account_no=acc_no).exists():
            raise forms.ValidationError(f"No bank account found with Account Number {acc_no}.")
        return acc_no

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is None or amount <= 0:
            raise forms.ValidationError("Transfer amount must be greater than $0.")
        if self.account and amount > self.account.balance:
            raise forms.ValidationError(
                f"Insufficient balance (${self.account.balance}) for this transfer."
            )
        return amount
