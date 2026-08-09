import pandas as pd
import random
import os

NUM_TEST_CASES = 5000

MODULES = ["Authentication", "Checkout", "Dashboard", "Profile", "Settings", "Search", "Payment", "Inventory"]
PRIORITIES = ["High", "Medium", "Low", "Critical"]
TAGS = ["regression", "smoke", "sanity", "ui", "api", "security", "performance"]

def generate_test_cases(num_cases=NUM_TEST_CASES):
    data = []
    for i in range(1, num_cases + 1):
        jira_id = f"VWO-{1000 + i}"
        module = random.choice(MODULES)
        priority = random.choice(PRIORITIES)
        tag_list = random.sample(TAGS, random.randint(1, 3))
        
        title = f"Verify {module.lower()} functionality for scenario {i}"
        steps = f"1. Navigate to {module}\n2. Perform action {i}\n3. Observe the result"
        expected = f"The {module.lower()} should behave correctly as expected for scenario {i}."
        
        data.append({
            "id": i,
            "jira_id": jira_id,
            "priority": priority,
            "module": module,
            "tags": ",".join(tag_list),
            "title": title,
            "steps": steps,
            "expected": expected
        })
        
    df = pd.DataFrame(data)
    
    # ensure data directory exists
    os.makedirs("data", exist_ok=True)
    
    output_path = "data/test_cases.csv"
    df.to_csv(output_path, index=False)
    print(f"Successfully generated {num_cases} test cases at {output_path}")

if __name__ == "__main__":
    generate_test_cases()
