class TestCounter:
    count = 0

    def __init__(self):
        TestCounter.count += 1


t1 = TestCounter()
t2 = TestCounter()

print(TestCounter.count)
