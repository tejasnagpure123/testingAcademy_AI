try:
    a = int(input("Enter num 1"))
    b = int(input("Enter num 2"))
    c = a / b
    print(c)
# Zero division by error


except (ZeroDivisionError, TypeError, NameError, ValueError ):
    print("Error bcuz of the zero division error")
