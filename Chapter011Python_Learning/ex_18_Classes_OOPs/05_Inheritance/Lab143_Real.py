class BaseTest:
    def __init__(self, browser):
        self.browser = browser

    def setup(self):
        print(f"Launching   {self.browser}")


class LoginTest(BaseTest):
    def run_test(self):
        self.setup()
        print("Running Login Test??")


class SignupTest(BaseTest):
    def run_test(self):
        self.setup()
        print("Running sign up Test??")


t = LoginTest("chrome")
t.run_test()
t = LoginTest("firefox")
t.run_test()
