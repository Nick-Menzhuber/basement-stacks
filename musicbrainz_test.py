import requests

headers = {
    'User-Agent': 'BasementStacks/1.0 (your@email.com)'
}

url = 'https://musicbrainz.org/ws/2/release-group'
params = {
    'artist': '9639cd52-c351-4a17-9797-58880e95a7ef',
    'type': 'album',
    'fmt': 'json',
    'limit': 100
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print("--- The Mountain Goats (ALL album-type release groups) ---")
results = []
for rg in data.get('release-groups', []):
    primary = rg.get('primary-type', '')
    secondary = rg.get('secondary-types', [])
    results.append((rg.get('first-release-date', '????')[:4], rg['title'], primary, secondary))

results.sort()
for year, title, primary, secondary in results:
    print(f"  {year} — {title} [{primary}{(' + ' + ', '.join(secondary)) if secondary else ''}]")