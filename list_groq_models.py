import os
import yaml
from groq import Groq

# Load config to get key
with open('config.yaml', 'r') as f:
    config = yaml.safe_load(f)

api_key = config.get('ai', {}).get('api_key') or os.environ.get('AI_API_KEY')
client = Groq(api_key=api_key)

print("Fetching available Groq models...")
models = client.models.list()

for m in models.data:
    print(f"ID: {m.id}, Owned by: {m.owned_by}")
