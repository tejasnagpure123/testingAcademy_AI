user_age = int(input("Enter your age: "))

if user_age >= 18:
    print("Eligible to vote")
else:
    print("Not eligible to vote")

print("You can go to Goa" if user_age > 18 else "You cannot go to Goa")
