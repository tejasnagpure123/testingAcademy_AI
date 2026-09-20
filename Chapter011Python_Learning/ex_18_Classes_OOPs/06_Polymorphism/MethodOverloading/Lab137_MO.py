class MathClass:
    def add(self, a, b):
        return a + b

    def add(self, a, b, c):
        return a + b + b


obj_ref = MathClass()
print(obj_ref.add(1, 2, 3))
# Python does not support traditional method overloading, it will always use the latest method

print(obj_ref.add(1, 2))
# TypeError: MathClass.add() missing 1 required positional argument: 'c'
