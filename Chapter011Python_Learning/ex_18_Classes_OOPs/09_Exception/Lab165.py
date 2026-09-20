try:
    a = int(input("Enter num 1"))
    b = int(input("Enter num 2"))
    c = a / b
    print(c)
except ValueError:
    print("Error bcuz of the ValueError error")

except (ZeroDivisionError, TypeError, NameError, ValueError):
    print("Error bcuz of the zero division error")
else:
    print(c)
finally:
    print("I will always execute")
