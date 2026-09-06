# Python stdin with input()
# First non repeating character in a string

user_input = input()
s = set()


def first_non_repeating_char(string):
    for char in string:
        if string.count(char) == 1:
            s.add(char)
            return char
        return None


print(first_non_repeating_char(user_input))
