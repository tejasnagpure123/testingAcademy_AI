def add_security(func):
    def wrapper():
        print("1. Before the function is called.")
        print("2. Add Helmet, Dashcam, Gloves, Knee Guards, License.")
        func()
        print("3. After the function is called.")
        print("4. Secure Driving, Leave all the items in the car, Drive Safely.")

    return wrapper


@add_security
def drive_ola_scotter():
    print("I am driving ola Scotter")


drive_ola_scotter()


@add_security
def drive_zypp_scotter():
    print("I am driving Zypp Scotter")
