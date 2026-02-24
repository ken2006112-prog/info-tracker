import google.generativeai as genai
import os
import yaml

with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

api_key = config.get('ai', {}).get('api_key') or os.environ.get('AI_API_KEY')
genai.configure(api_key=api_key)

print("Listing available models...")
for m in genai.list_models():
    print(f"name: {m.name}")
    print(f"supported_generation_methods: {m.supported_generation_methods}")
