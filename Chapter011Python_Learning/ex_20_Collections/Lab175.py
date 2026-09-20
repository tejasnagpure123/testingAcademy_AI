import os

file_path = os.path.join(os.path.dirname(__file__), "testdata.txt")
with open(file_path, "r") as file_data:
    print(file_data.read())
