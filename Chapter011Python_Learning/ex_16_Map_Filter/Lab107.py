test_results = ["PASS", "FAIL", "PASS", "FAIL", "SKIP"]

pass_give = list(filter(lambda x: x == "PASS", test_results))
print(pass_give)
