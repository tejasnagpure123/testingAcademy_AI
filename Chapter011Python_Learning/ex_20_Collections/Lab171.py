from collections import *

# list -> Collection on itesms
# tuple -> List but it cannot be modified
# set  -> No duplicates
# dict -> key and value pair

t = (34, True, 123)

info = namedtuple("info", ["name", "age", "ismarried", "number"])
t = info("Tejas", 33, True, 9.8)
print(t)


from collections import defaultdict

groups = defaultdict(list)
for word in ["apple", "avacado", "banana"]:
    groups[word[0]].append(word)
print(groups)

counts = defaultdict(int)
uniques = defaultdict(set)
nested = defaultdict(lambda: defaultdict(int))
print(counts)
