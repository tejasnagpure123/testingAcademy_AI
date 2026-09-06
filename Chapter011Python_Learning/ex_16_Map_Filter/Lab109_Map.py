number = [1, 2, 3, 4, 5]


def sq(x):
    return x**2


# Map-> Apply the funtion on each element and give you the same size list

all_number = list(map(sq, number))
print(all_number)
