import json
from app import app, db
from models import Artist, Release

with app.app_context():
    artists = []
    for a in Artist.query.all():
        artists.append({
            'discogs_artist_id': a.discogs_artist_id,
            'sort_name': a.sort_name,
            'custom_profile': a.custom_profile,
            'hidden': a.hidden,
        })

    releases = []
    for r in Release.query.all():
        releases.append({
            'discogs_id': r.discogs_id,
            'master_id': r.master_id,
            'short_title': r.short_title,
            'sort_order': r.sort_order,
            'hidden': r.hidden,
            'notes': r.notes,
            'mood': r.mood,
        })

    with open('custom_data_export.json', 'w') as f:
        json.dump({'artists': artists, 'releases': releases}, f, indent=2, default=str)

    print(f"Exported {len(artists)} artists and {len(releases)} releases")