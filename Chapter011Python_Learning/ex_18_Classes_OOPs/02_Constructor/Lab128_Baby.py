class Baby:
    name: None

    def __init__(self, name): 
        self.name = name

    def printName(self):
        print(self.name)


b = Baby("gugu")
b.printName()
