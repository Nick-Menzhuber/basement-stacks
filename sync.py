import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from app import app, db
from models import Artist, Release, Format

load_dotenv()

token = os.getenv('DISCOGS_TOKEN')
username = os.getenv('DISCOGS_USERNAME')

headers = {
    'Authorization': f'Discogs token={token}',
    'User-Agent': 'BasementStacks/1.0'
}

def sync_item(item):
    basic = item['basic_information']
    discogs_id = str(item['id'])
    
    # Get or create artist
    artist_name = basic['artists'][0]['name']
    artist = Artist.query.filter_by(name=artist_name).first()
    
    if not artist:
        artist = Artist(
            name=artist_name,
            sort_name=artist_name
        )
        db.session.add(artist)
        db.session.flush()
    
    # Get or create release
    release = Release.query.filter_by(discogs_id=discogs_id).first()
    
    if not release:
        release = Release(
            title=basic['title'],
            artist_id=artist.id,
            release_year=basic.get('year'),
            discogs_id=discogs_id,
            cover_image_url=basic.get('cover_image'),
            genre=basic['genres'][0] if basic.get('genres') else None,
            date_added=datetime.fromisoformat(item['date_added'].replace('Z', '+00:00')),
            is_customized=False
        )
        db.session.add(release)
        db.session.flush()
    
    # Add formats
    for fmt in basic.get('formats', []):
        format_name = fmt['name']
        existing = Format.query.filter_by(release_id=release.id, format_name=format_name).first()
        if not existing:
            new_format = Format(
                release_id=release.id,
                format_name=format_name
            )
            db.session.add(new_format)

    db.session.commit()

def sync_collection():
    page = 1
    total_pages = 1

    while page <= total_pages:
        url = f'https://api.discogs.com/users/{username}/collection/folders/0/releases?page={page}&per_page=100'
        response = requests.get(url, headers=headers)
        data = response.json()

        total_pages = data['pagination']['pages']
        print(f"Syncing page {page} of {total_pages}...")

        for item in data['releases']:
            sync_item(item)

        page += 1

    print("Sync complete!")

if __name__ == '__main__':
    with app.app_context():
        sync_collection()   