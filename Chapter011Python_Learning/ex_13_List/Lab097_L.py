my_list = [1, 2, 3, 4, 5]

my_list[0] = "Pramod"
my_list[1] = "Dutta"
my_list[1] = "Dutta"

print(my_list)
# List is mutable in nature it can be changed

for element in my_list:
    print(element)

for i in range(1, 5):
    print(i)


my_list = [1, 2, 3]
print("Element at index 0: ", my_list[0])
print("Element at index 1: ", my_list[1])


my_list.append(4)
print("My list after append", my_list)


my_list.extend([5, 6, 7, 8])
print("My list after extend", my_list)


my_list.insert(1, "Phoenix")
print("My list after Insert", my_list)

my_list[1] = "Rise"
print("My list after Rise", my_list)

my_list.remove("Rise")
print("My list after Remove", my_list)

my_Copy_list = my_list.copy()
print("My Copy list", my_Copy_list)
