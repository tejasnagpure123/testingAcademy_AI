set1 = set(["TestingAcademy", "For", "TestingAcademy."])
print(set1)
print(type(set1))
print(len(set1))

for i in set1:
    print(i)  # Output: TestingAcademy For - Iterating through the set elements


set1.add("Python")  # Adding an element to the set
print(
    "Added element:", set1
)  # Output: {'TestingAcademy', 'For', 'Python'} - The element 'Python' is added to the set


