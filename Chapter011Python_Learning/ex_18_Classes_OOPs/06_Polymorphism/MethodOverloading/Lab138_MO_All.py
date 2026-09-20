class Person:
    def say_name(self, name):
        print("Hi", name)

    def say_name(self, name, last_name="Nagpure"):
        print("Hi", name, last_name)


t = Person()
# Since it always works with the recent method , It will work with custom value passed, or third value passed
# Or else it will throw error
t.say_name("Tejas")
t.say_name("Tejas", "Dipak")
