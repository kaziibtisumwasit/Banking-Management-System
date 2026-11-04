DEPOSIT = 1
WITHDRAWAL = 2
WITHDEAWAL = 2  # Alias kept for backward compatibility
LOAN = 3
LOAN_PAID = 4
MONEY_SEND = 5
MONEY_RECEIVED = 6

TRANSACTION_TYPE = (
    (DEPOSIT, "Deposit"),
    (WITHDRAWAL, "Withdrawal"),
    (LOAN, "Loan"),
    (LOAN_PAID, "Loan Paid"),
    (MONEY_SEND, "Money Send"),
    (MONEY_RECEIVED, "Money Received"),
)
