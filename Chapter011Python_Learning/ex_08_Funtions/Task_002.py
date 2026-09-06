# Create a program to sum of three number from the user input,
# if user doesn't enter any number', use default as 100, 200, 300
# Logic Building
# Step 1 - I/O and O/P
# I/O -  int
# O/P - int
# Step 2 - Rough Logic
# return n1+n2+n3


def sum_three(a=100, b=200, c=300):
    return a + b + c


num1 = int(input("Enter first number: "))
num2 = int(input("Enter second number: "))
num3 = int(input("Enter third number: "))

result = sum_three()
print(result)


result1 = sum_three(num1, num2)
print(result1)

result2 = sum_three(num1, num2, num3)
print(result2)
