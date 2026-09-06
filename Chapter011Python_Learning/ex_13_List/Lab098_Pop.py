squares = [1, 2, 3, 4, 5]
print(squares)

print(squares.pop())

print(squares)

print(squares.pop(1))

print(squares)


squares.clear()
print(squares)


numbers = [10, 30, 45, 55, 6, 3, 5, 6, 8, 8, 4, 2]
print(numbers.index(45))
print(numbers.count(6))


numbers.sort()
print(numbers)

numbers.sort(reverse=True)
print(numbers)

print(numbers[1:4])


print("apple" in numbers)
print(30 in numbers)

l = list(range(1, 5))
print(l)

matrix = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
print(matrix[1][2])

del numbers[0]
print(numbers)
