age = int(input("Enter your age: "))
if age >= 18:
    print("You are eligible to vote.")
else:
    print("You are not eligible to vote.")


age = int(input("Enter your age\n: ").strip())
if (age <= 0) or age > 130:
    print("Invalid age entered.")
else:
    if age >= 18:
        print("You are eligible to vote.")
    else:
        print("You are not eligible to vote.")
