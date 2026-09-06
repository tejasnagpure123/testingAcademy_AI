import time


def print_logs(func):
    def wrapper():
        print("Start the logs")
        func()
        print("End the logs")

    return wrapper


def time_decorator(func):
    def wrapper():
        start_time = time.time()
        print(start_time)
        func()
        end_time = time.time()
        print(end_time)
        print("Total time taken by this function is : ", end_time - start_time)

    return wrapper


@time_decorator
@print_logs
def test_ui():
    print("Add a funtion ,this time taken by this function 1")
    time.sleep(2)


@time_decorator
@print_logs
def test_ui2():
    print("Add a funtion ,this time taken by this function 2")
    time.sleep(5)


test_ui()
test_ui2()
