class Home:
    def __init__(self):
        self.public_var = "father"
        self._protected_var = "brother"
        self.__private_var = "baby"

    def mom(self):
        print(self.__private_var)
        self.__wife()

    def __wife(self):
        print("Private Wife")
