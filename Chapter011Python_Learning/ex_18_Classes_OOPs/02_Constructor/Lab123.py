class MobilePhone:
    model = None

    def __init__(self):
        print("This is constructor, I will be called when the Object is Created")
        print(self.model)

    def talk(self):
        print("Normal F(n)")


iphone = MobilePhone()
iphone.talk()
