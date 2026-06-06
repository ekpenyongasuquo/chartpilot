import os
from dotenv import load_dotenv
load_dotenv('../.env')

api_key = os.getenv('DASHSCOPE_API_KEY')
print(f"Using key: {api_key[:20]}...")

# Try each endpoint until one works
endpoints = [
    "https://api.qwencloud.com/v1",
    "https://api.qwencloud.com",
    "https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
    "https://dashscope.aliyuncs.com/compatible-mode/v1",
]

from openai import OpenAI

for base_url in endpoints:
    print(f"\nTrying: {base_url}")
    try:
        client = OpenAI(api_key=api_key, base_url=base_url)
        r = client.chat.completions.create(
            model="qwen-max",
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=5,
        )
        print(f"SUCCESS with: {base_url}")
        print(f"Response: {r.choices[0].message.content}")
        break
    except Exception as e:
        print(f"FAIL: {str(e)[:120]}")