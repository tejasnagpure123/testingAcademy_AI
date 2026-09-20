from abc import ABC, abstractmethod


class Father(ABC):
    def __init__(self, name):
        self.name = name
        print("Loan taken by: ", self.name)

    @abstractmethod
    def loan(self):
        pass


class Amit(Father):
    def loan(self):
        print("Giving the 50K loan")


amit = Amit("Baba sharma")
amit.loan()
