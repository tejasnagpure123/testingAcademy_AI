class BaseTest:
    def run(self):
        print("Running the Base Test")


class LoginTest(BaseTest):
    def run(self):
        print("Runnning Login Test")


t1 = BaseTest()
t1.run()
t = LoginTest()
t.run()
