import requests

try:
    url = input("Enter the url")

    response = requests.get(url, timeout=3)
    print(response.status_code)
except requests.exceptions.ConnectionError:
    print("Error due to wrong url or connection failed")
except requests.exceptions.Timeout:
    print("Timeout error, not able to laod the URL.")
except Exception as e:
    print(e)
