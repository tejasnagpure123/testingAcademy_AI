list_Of_unique_numbers = {1, 2, 3, 3, 5, 6, 7, 8, 8, 10}
print(list_Of_unique_numbers)

list1 = [55, 2, 3, 4, 34, 6, 543, 8, 9]
set1 = set(list1)
print(set1)


t = ("TheTesting", "For", "TheTesting")
print(t)

print(set(t))  # Output: {'TheTesting', 'For'} - Duplicates are removed


mixed = (1, "QA", True, 3.5)
print(
    set(mixed)
)  # Output: {1, 'QA', True, 3.5} - Sets can contain different data types

mixed1 = (1, "QA", False, 3.5)
print(
    set(mixed1)
)  # Output: {1, 'QA', False, 3.5} - Sets can contain different data types


empty = set()
print(empty)  # Output: set() - An empty set is created using set() function

for i in mixed:
    print(i)  # Output: 1 QA True 3.5 - Iterating through the set elements

mixed2 = {1, "QA", True, 3.5}

mixed2.add(1022)  # Adding an element to the set
print(
    "Added element:", mixed2
)  # Output: {1, 'QA', True, 3.5, 10} - The element 10 is added to the set

mixed2.remove("QA")  # Removing an element from the set
print(
    "After removal:", mixed2
)  # Output: {1, True, 3.5, 10} - The element 'QA' is removed from the set

a = {1, 2, 3}
b = {3, 4, 5}

print(a.union(b))  # Output: {1, 2, 3, 4, 5} - Union of sets a and b
print(a | b)  # Output: {1, 2, 3, 4, 5} - Union of sets a and b using | operator

print(a.intersection(b))  # Output: {3} - Intersection of sets a and b
print(a & b)  # Output: {3} - Intersection of sets a and b


print(a - b)  # Output: {1, 2} - Difference of sets a and b
print(b - a)  # Output: {4, 5} - Difference of sets b and a
