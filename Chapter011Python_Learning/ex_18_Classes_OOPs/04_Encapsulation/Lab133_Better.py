class Car:
    def __init__(self):
        self.public_pramod = "Pramod"
        self._protected_baby = "Pass@123"
        self.__private_baby = "Pass@123"

    def nany(self):
        self.__password_yogesh_private = "345"


object_ref = Car()
print(object_ref.public_pramod)


object_ref.nany()
