inputString = "Aeroplane"
vowel = "aeiou"
vowel_count = 0
result = list()

for i in inputString:
    if i in vowel:
        vowel_count = vowel_count + 1
        result.append(i)

print(vowel_count)
print(result)
