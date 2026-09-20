def VWo_Login(user):
    if user != "admin":
        raise Exception("Unauthorized Access")
    return "Welcome admn"


print(VWo_Login("admin"))
