from django.urls import path
from . import views

urlpatterns = [
    path("diposit/", views.DepositeMoneyView.as_view(), name="diposit"),
    path("deposit/", views.DepositeMoneyView.as_view(), name="deposit"),
    path("withdrawmoney/", views.WithdrawMoneyView.as_view(), name="withdeaw"),
    path("withdraw/", views.WithdrawMoneyView.as_view(), name="withdraw"),
    path("transaction_report/", views.TransactionRepostView.as_view(), name="transaction_report"),
    path("loan_request/", views.LoanRequestView.as_view(), name="loan_request"),
    path("loans/", views.LoanListView.as_view(), name="loan_list"),
    path("pay_loan/<int:loan_id>/", views.PayLoanView.as_view(), name="payloan"),
    path("pay_loan/<int:loan_id>/", views.PayLoanView.as_view(), name="pay_loan"),
    path("transfer_money/", views.TransferMoneyView.as_view(), name="transfer_money"),
]
