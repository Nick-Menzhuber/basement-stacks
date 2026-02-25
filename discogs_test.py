import requests
import os
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('DISCOGS_TOKEN')
username = 'nickmenzhuber'

url = f'https://api.discogs.com/users/nickmenzhuber/collection/folders/0/releases'

headers = {
    'Authorization': f'Discogs token={token}',
    'User-Agent': 'BasementStacks/1.0'
}

response = requests.get(url, headers=headers)
data = response.json()

print(f"Status code: {response.status_code}")
print(f"Total items in collection: {data['pagination']['items']}")
first_item = data['releases'][0]
print(first_item)

master_url = f'https://api.discogs.com/masters/28547'
master_response = requests.get(master_url, headers=headers)
master_data = master_response.json()
print(master_data)
