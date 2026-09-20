class TestSuite:
    def info(self):
        print("This is GF - Step1")


class BaseTest(TestSuite):
    def setup(self):
        print("Base test - F - Step 2")


class UITest(BaseTest):
    def run(self):
        self.info()
        self.setup()
        print("Running Test Case")


test = UITest()
test.run()
