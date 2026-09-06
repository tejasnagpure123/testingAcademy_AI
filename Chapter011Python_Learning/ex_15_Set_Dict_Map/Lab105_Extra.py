squares = {x**2 for x in range(5)}
print(squares)


# Frozenset is an immutable version of a set. It cannot be modified after creation, which means you cannot add or remove elements from a frozenset. However, you can perform operations like union, intersection, and difference with frozensets.
my_list = [1, 2, 3, 3]
f_set = frozenset(my_list)
# f_set.add(4)  # This will raise an AttributeError because frozensets are immutable
print(f_set)
