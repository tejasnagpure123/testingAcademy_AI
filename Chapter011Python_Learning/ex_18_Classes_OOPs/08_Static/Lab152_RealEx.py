class ExcelReader:
    @staticmethod
    def readExcelFile():
        print("Reading from excel")


class MYSQLConnection:
    @staticmethod
    def readMySqlFile():
        print("Reading from my sql")


class TC1:
    def runTC(self):
        ExcelReader.readExcelFile()
        MYSQLConnection.readMySqlFile()
        print("Hi")


tc1 = TC1()
tc2 = TC1()
tc1.runTC()
tc2.runTC()
