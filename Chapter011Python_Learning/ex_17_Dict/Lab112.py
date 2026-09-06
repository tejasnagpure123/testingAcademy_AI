myDict = {
    "name": "Tejas",
    "age": 34,
    "role": "SDET",
    "exp": 5,
}

print(myDict)
print(myDict["age"])
print(myDict["role"])


myDict["role"] = "Automation Tester"
print(myDict)

del myDict["age"]
print(myDict)

for key, value in myDict.items():
    print(key, value)


print("age" in myDict)
