class BaseTest:
    driver = "Chrome"
    __driver = "Firefox"

    def setUp(self):
        print("Base Test set up is done here")


class LoginTest(BaseTest):
    def run(self):
        self.setUp()
        print("Runnin the test case -> " + self.driver)


t = LoginTest()

t.run()
