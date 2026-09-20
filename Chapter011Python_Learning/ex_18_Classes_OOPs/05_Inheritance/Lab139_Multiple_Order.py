class Father1:
    def money(self):
        print("F1 Money")


class Father2:
    def money(self):
        print("F2 Money")


class Child(Father2, Father1):
    def give_Money(self):
        print("son")
        self.money()


c = Child()
c.give_Money()
