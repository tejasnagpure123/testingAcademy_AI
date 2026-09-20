class TestSuite:
    def info(self):
        print("Test suite information")


class BaseTest(TestSuite):
    def setup(self):
        print("Base setup")

    def run(self):
        print("Base Test execution")


class LoginTest(BaseTest):
    def run(self):
        print("Login test execution")


class APITest(BaseTest):
    def run(self):
        print("API Test execution")


t = LoginTest()
t1 = APITest()
t2 = BaseTest()

t.run()
t1.run()
t2.run()
