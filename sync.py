import requests
import re
import os
import time 
import json
import unicodedata
from dotenv import load_dotenv
from datetime import datetime
from app import app, db
from models import Artist, Release, Format, Membership

load_dotenv()

token = os.getenv('DISCOGS_TOKEN')
username = os.getenv('DISCOGS_USERNAME')

headers = {
    'Authorization': f'Discogs token={token}',
    'User-Agent': 'BasementStacks/1.0'
}

def clean_artist_name(name):
    return re.sub(r'\s*\(\d+\)\s*$', '', name).strip()

def clean_discogs_markup(text):
    if not text:
        return None
    # Remove [a=Artist Name] style links, keep the name
    text = re.sub(r'\[a\d*=([^\]]+)\]', r'\1', text)
    # Remove [m=12345] master links entirely
    text = re.sub(r'\[m=\d+\]', '', text)
    # Remove [l=12345] label links entirely  
    text = re.sub(r'\[l=\d+\]', '', text)
    # Remove [url=...][/url] style links, keep the text
    text = re.sub(r'\[url=[^\]]+\]([^\[]+)\[\/url\]', r'\1', text)
    # Remove [r=12345] release links entirely
    text = re.sub(r'\[r=\d+\]', '', text)
    return text.strip()

def normalize_search(text):
    if not text:
        return None
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii').lower()

def sync_artist(artist):
    if not artist.discogs_artist_id:
        return
    
    url = f'https://api.discogs.com/artists/{artist.discogs_artist_id}'
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return
    
    data = response.json()
    
    # Profile and URLs
    artist.profile = clean_discogs_markup(data.get('profile', None))
    artist.urls = json.dumps(data.get('urls', []))
    artist.videos = json.dumps(data.get('videos', []))
    
    # Primary image
    images = data.get('images', [])
    primary = next((img for img in images if img['type'] == 'primary'), None)
    if primary:
        artist.image_url = primary['uri']
    
    # Members (for bands)
    for member in data.get('members', []):
        member_name = clean_artist_name(member['name'])
        member_artist = Artist.query.filter_by(discogs_artist_id=str(member['id'])).first()
        if not member_artist:
            member_artist = Artist(
                name=member_name,
                sort_name=member_name,
                discogs_artist_id=str(member['id'])
            )
            db.session.add(member_artist)
            db.session.flush()
        
        existing = Membership.query.filter_by(
            artist_id=member_artist.id,
            group_id=artist.id
        ).first()
        if not existing:
            membership = Membership(
                artist_id=member_artist.id,
                group_id=artist.id
            )
            db.session.add(membership)
    
    # Groups (for solo artists)
    for group in data.get('groups', []):
        group_name = clean_artist_name(group['name'])
        group_artist = Artist.query.filter_by(discogs_artist_id=str(group['id'])).first()
        if not group_artist:
            group_artist = Artist(
                name=group_name,
                sort_name=group_name,
                discogs_artist_id=str(group['id'])
            )
            db.session.add(group_artist)
            db.session.flush()
        
        existing = Membership.query.filter_by(
            artist_id=artist.id,
            group_id=group_artist.id
        ).first()
        if not existing:
            membership = Membership(
                artist_id=artist.id,
                group_id=group_artist.id
            )
            db.session.add(membership)
    
    db.session.commit()
    time.sleep(1)


def sync_item(item):
    basic = item['basic_information']
    discogs_id = str(item['id'])
    master_id = str(basic.get('master_id', '')) if basic.get('master_id') else None

    # Fetch master data if available
    cover_image = basic.get('cover_image')
    release_year = basic.get('year')
    tracklist_json = None

    if master_id:
        master_url = f'https://api.discogs.com/masters/{master_id}'
        master_response = requests.get(master_url, headers=headers)
        if master_response.status_code == 200:
            master_data = master_response.json()
            images = master_data.get('images', [])
            primary = next((img for img in images if img['type'] == 'primary'), None)
            if primary:
                cover_image = primary['uri']
            release_year = master_data.get('year', release_year)
            tracklist_json = json.dumps(master_data.get('tracklist', []))
        time.sleep(1)

    individual_tracklist_json = None
    individual_url = f'https://api.discogs.com/releases/{discogs_id}'
    individual_response = requests.get(individual_url, headers=headers)
    if individual_response.status_code == 200:
        individual_data = individual_response.json()
        individual_tracklist_json = json.dumps(individual_data.get('tracklist', []))
    time.sleep(1)

    # Get or create artist
    artist_name = clean_artist_name(basic['artists'][0]['name'])
    artist = Artist.query.filter_by(name=artist_name).first()

    if not artist:
        artist = Artist(
            name=artist_name,
            sort_name=clean_artist_name(basic['artists'][0]['name']),
            discogs_artist_id=str(basic['artists'][0]['id']),
            search_name=normalize_search(artist_name)
        )
        db.session.add(artist)
        db.session.flush()
    else:
        artist.search_name = normalize_search(artist_name)

    # Get or create release using master_id
    lookup_id = master_id if master_id else discogs_id
    release = Release.query.filter_by(master_id=lookup_id).first() if master_id else Release.query.filter_by(discogs_id=discogs_id).first()

    if not release:
        release = Release(
            title=basic['title'],
            artist_id=artist.id,
            release_year=release_year,
            discogs_id=discogs_id,
            master_id=master_id,
            cover_image_url=cover_image,
            genre=basic['genres'][0] if basic.get('genres') else None,
            date_added=datetime.fromisoformat(item['date_added'].replace('Z', '+00:00')),
            tracklist=tracklist_json,
            individual_tracklist=individual_tracklist_json,
            is_customized=False
        )
        db.session.add(release)
        db.session.flush()

    # Normalize and filter formats
    approved_formats = set()
    for fmt in basic.get('formats', []):
        name = fmt['name']
        descriptions = fmt.get('descriptions', [])

        if 'Vinyl' in name:
            if '7"' in descriptions:
                approved_formats.add('7"')
            else:
                approved_formats.add('Vinyl')
        elif name == 'CD':
            approved_formats.add('CD')
        elif name == 'Cassette':
            approved_formats.add('Cassette')
        elif name == 'SACD':
            approved_formats.add('CD')
        # Everything else (Box Set, DVD, All Media, etc.) is ignored

    for format_name in approved_formats:
        existing = Format.query.filter_by(release_id=release.id, format_name=format_name).first()
        if not existing:
            new_format = Format(
                release_id=release.id,
                format_name=format_name,
                discogs_release_id=discogs_id
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

    print("Syncing artist data...")
    artist = Artist(
    name=artist_name,
    sort_name=clean_artist_name(basic['artists'][0]['name']),
    discogs_artist_id=str(basic['artists'][0]['id']),
    search_name=normalize_search(artist_name),
    hidden=False
)
    for i, artist in enumerate(artists):
        print(f"Syncing artist {i+1} of {len(artists)}: {artist.name}")
        sync_artist(artist)

    print("Sync complete!")

if __name__ == '__main__':
    with app.app_context():
        sync_collection()