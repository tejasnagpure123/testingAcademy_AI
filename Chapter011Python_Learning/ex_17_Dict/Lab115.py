student_info = {
    "name": "Tejas",
    "age": 34,
    "address": {"HomeAddress": "MH", "OfficeAddress": "Pune"},
}
# print(student_info)


student_info2 = {
    "name": "Saurabh",
    "age": 30,
    "address": {"HomeAddress": "MH", "OfficeAddress": "Wardha"},
}
# print(student_info2)


student_info3 = {
    "name": "Ankita",
    "age": 30,
    "address": {"HomeAddress": "MH", "OfficeAddress": "Pohi"},
}
# print(student_info2)

student_list = [student_info, student_info2, student_info3]
print(student_list)

print(student_list[0]["address"]["OfficeAddress"])
