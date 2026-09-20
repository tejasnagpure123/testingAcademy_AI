import os

try:
    file_path = os.path.join(os.path.dirname(__file__), "testdata.txt")
    with open(file_path, "r") as file:
        content = file.read()
        print(content)
except FileNotFoundError as fnfe:
    print(fnfe)
