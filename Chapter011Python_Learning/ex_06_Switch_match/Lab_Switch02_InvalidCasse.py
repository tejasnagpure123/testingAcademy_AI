print("Enter the test you want to run")
testType = input("Enter the type of test: API, UI, Performance, Security\n")

match testType:
    case "API":
        print("Running API test")
    case "UI":
        print("Running UI test")
    case "Performance":
        print("Running Performance test")
    case "Security":
        print("Running Security test")
    case _:
        print("Invalid test type")
