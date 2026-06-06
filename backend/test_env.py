import os
from dotenv import load_dotenv

load_dotenv('../.env')
key = os.getenv('DASHSCOPE_API_KEY', 'NOT FOUND')

if key == 'NOT FOUND':
    print('ERROR: .env file not found or DASHSCOPE_API_KEY missing')
elif key == 'sk-your-dashscope-key-here' or key == 'placeholder':
    print('ERROR: API key is still the placeholder value - add your real key')
elif len(key) > 15:
    print(f'OK: Key found - starts with {key[:15]}...')
else:
    print(f'ERROR: Key too short - value is: {key}')