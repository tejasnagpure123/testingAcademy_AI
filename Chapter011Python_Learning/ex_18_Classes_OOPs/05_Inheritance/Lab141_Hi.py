class BaseTest:
    def setup(self):
        print("Setup from Base Test")


class LoginTest(BaseTest):
    def run(self):
        print("Running Login Tets")


class Signup(BaseTest):
    def run(self):
        print("Running Signup  Test")


LoginTest().setup()
LoginTest().run()
Signup().setup()
Signup().run()
