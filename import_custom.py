import json
from app import app, db
from models import Artist, Release

with open('custom_data_export.json', 'r') as f:
    data = json.load(f)

with app.app_context():
    artist_count = 0
    for a in data['artists']:
        if not a['discogs_artist_id']:
            continue
        artist = Artist.query.filter_by(discogs_artist_id=a['discogs_artist_id']).first()
        if artist:
            artist.sort_name = a['sort_name']
            artist.custom_profile = a['custom_profile']
            artist.hidden = a['hidden']
            artist_count += 1

    release_count = 0
    for r in data['releases']:
        release = None
        if r['master_id']:
            release = Release.query.filter_by(master_id=r['master_id']).first()
        if not release and r['discogs_id']:
            release = Release.query.filter_by(discogs_id=r['discogs_id']).first()
        if release:
            release.short_title = r['short_title']
            release.sort_order = r['sort_order']
            release.hidden = r['hidden']
            release.notes = r['notes']
            release.mood = r['mood']
            release_count += 1

    db.session.commit()
    print(f"Updated {artist_count} artists and {release_count} releases")