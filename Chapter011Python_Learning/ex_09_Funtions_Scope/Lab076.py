public_toilet = "PB"


def home():
    private_toilet = "PT"
    print(public_toilet)
    print(private_toilet)


def stranger():
    print(public_toilet)
    # print(private_toilet)  # This will raise an error because private_toilet is not accessible here
