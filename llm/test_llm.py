import requests
import json

api_key = "sk-f8adf4015fb548169eb4d3c19afc7537"
url = "https://api.deepseek.com/v1/chat/completions"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}
data = {
    "model": "deepseek-chat",
    "messages": [{"role": "user", "content": "你好"}]
}

resp = requests.post(url, headers=headers, json=data)
print("状态码:", resp.status_code)
print("返回内容:", resp.text)
