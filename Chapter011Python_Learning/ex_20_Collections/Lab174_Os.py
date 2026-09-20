import os

print(os.getcwd())
full_path = os.path.join(
    os.getcwd(),
    r"Chapter011Python_Learning\ex_20_Collections\tejas.txt",
)
print(full_path)

with open(full_path, "r") as file:
    print(file.read())
