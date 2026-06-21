import requests

url = "http://127.0.0.1:8000/api/v1/ai/recommendations"

payload = {
    "query": "适合办公久坐的椅子",
    "limit": 5
}

res = requests.post(url, json=payload)

print("状态码:", res.status_code)
print("返回:", res.json())