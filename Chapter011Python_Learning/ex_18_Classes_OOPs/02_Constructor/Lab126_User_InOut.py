class Person:
    name = None
    age = None
    phone = None
    occupation = None


def __init__(self):
    print("Lets take a user input, Please share the name, age, phone , occupation")
    self.name = input("Enter the name\n")
    self.age = input("Enter the age\n")
    self.phone = input("Enter the phone\n")
    self.occupation = input("Enter the occupation\n")


def display_Values(self):
    print(
        "Name is: ",
        self.name,
        " Age is: ",
        self.age,
        "Phone is: ",
        self.phone,
        "Occupation is: ",
        self.occupation,
    )


amit = Person()
amit.display_Values()
