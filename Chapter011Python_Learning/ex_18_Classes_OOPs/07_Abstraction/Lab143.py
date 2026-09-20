# Abstraction
# Hide details  and show what is required

# car: key       -> __private
#     tires     -> public

from abc import ABC, abstractmethod


class Animal(ABC):

    def __init__(self, name):
        self.name = name

    @abstractmethod
    def sound(self):
        pass


class Dog(Animal):
    def sound(self):
        print("Bark !")


dog = Dog("Dog")
dog.sound()
