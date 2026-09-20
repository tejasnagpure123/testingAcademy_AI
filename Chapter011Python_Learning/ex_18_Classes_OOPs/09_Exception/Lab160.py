a = int(input("Enter num 1"))
b = int(input("Enter num 2"))

try:
    c = a / b
    print(c)
# Zero division by error


except ZeroDivisionError:
    print("Error bcuz of the zero division error")
