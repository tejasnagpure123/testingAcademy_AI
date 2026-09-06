def decorator1(func):
    def wrapper():
        print("Decorator 1 is executed before the function is called.")
        func()
        print("Decorator 1 is End before the function is called.")

    return wrapper


def decorator2(func):
    def wrapper():
        print("Decorator 2 is executed before the function is called.")
        func()
        print("Decorator 2 is End before the function is called.")

    return wrapper


@decorator1
@decorator2
def say_hello():
    print("Hello")


say_hello()
