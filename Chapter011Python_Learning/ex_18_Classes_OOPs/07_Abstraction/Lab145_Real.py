from abc import ABC, abstractmethod


class BrowserManager(ABC):
    @abstractmethod
    def start(self):
        pass

    def stop(self):
        print("Stop command, common")


class ChromeBrowser(BrowserManager):

    def start(self):
        # t = ChromeDriver()
        print("We are starting the chrome")


tc = ChromeBrowser()
tc.start()
tc.stop()
