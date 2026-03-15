import requests

url = "https://fl-17-240.zhdk.cloud.switch.ch/containers"
response = requests.get(url)
data = response.json()

print(data)
