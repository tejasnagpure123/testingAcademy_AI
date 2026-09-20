class Bank:

    def __init__(self, account_number, balance):
        self.balance = balance
        self.__account_number = account_number

    def check_balance(self):
        print(self.balance)

    def deposit(self, amount):
        self.balance = self.balance + amount

    def show_me_account_number(self, is_auth):
        if is_auth == True:
            print(self._account_number)
        else:
            print("Not Allowed")


icici = Bank(7798776284, 100)
icici.deposit(100)
icici.check_balance()


icici.show_me_account_number(True)
