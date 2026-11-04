from django.db import models
from accounts.models import UserBankAccount
from .constance import TRANSACTION_TYPE


class Transaction(models.Model):
    account = models.ForeignKey(
        UserBankAccount, related_name="transaction", on_delete=models.CASCADE
    )
    amount = models.DecimalField(decimal_places=2, max_digits=12)
    balance_after_transaction = models.DecimalField(decimal_places=2, max_digits=12)
    transaction_type = models.IntegerField(choices=TRANSACTION_TYPE, null=True)
    time_stamp = models.DateTimeField(auto_now_add=True)
    loan_approve = models.BooleanField(default=False)

    class Meta:
        ordering = ["time_stamp"]

    @property
    def timestamp(self):
        return self.time_stamp
