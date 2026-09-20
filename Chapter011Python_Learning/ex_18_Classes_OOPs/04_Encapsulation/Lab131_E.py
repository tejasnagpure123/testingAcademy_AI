class VWOLoginPage:
    def __init__(self, email_arg, pass_arg):
        self.email = email_arg
        self.password = pass_arg

    def login_confirm(self):
        if self.email == "pramod@gmail.com" and self.password == "pass123":
            print("Allowed to print")
        else:
            print("login Failed")


email = input("Enter the VWO email")
password = input("Enter the Vwo login password")


vwo_object_reference = VWOLoginPage(email, password)
vwo_object_reference.login_confirm()
