class Dog:
    name = None
    breed = None
    height = None
    weight = None
    race = None

    def __init__(self, nameGiven, breedGiven):
        print("Param C")
        self.name = nameGiven
        self.breed = breedGiven

    def bark(self):
        print("Barking ! ->", self.name, "with breed as", self.breed)

    def talk(self):
        print("Talking")


chow = Dog("chow", "mastiff")
chow.bark()


desi = Dog("rancho", "desi")
desi.bark()
