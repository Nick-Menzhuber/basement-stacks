import json
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()

db_url = os.environ.get('DATABASE_URL')

with open('custom_data_export.json', 'r') as f:
    data = json.load(f)

def get_conn():
    return psycopg2.connect(db_url)

conn = get_conn()
cur = conn.cursor()

artist_count = 0
for a in data['artists']:
    if not a['discogs_artist_id']:
        continue
    try:
        cur.execute("""
            UPDATE artists SET sort_name=%s, custom_profile=%s, hidden=%s
            WHERE discogs_artist_id=%s
        """, (a['sort_name'], a['custom_profile'], a['hidden'], a['discogs_artist_id']))
        conn.commit()
        if cur.rowcount:
            artist_count += 1
    except Exception as e:
        print(f"Reconnecting after error on artist {a['discogs_artist_id']}: {e}")
        try:
            conn.close()
        except:
            pass
        conn = get_conn()
        cur = conn.cursor()

release_count = 0
for r in data['releases']:
    try:
        cur.execute("""
            UPDATE releases SET short_title=%s, sort_order=%s, hidden=%s, notes=%s, mood=%s
            WHERE master_id=%s OR discogs_id=%s
        """, (r['short_title'], r['sort_order'], r['hidden'], r['notes'], r['mood'], r['master_id'], r['discogs_id']))
        conn.commit()
        if cur.rowcount:
            release_count += 1
    except Exception as e:
        print(f"Reconnecting after error on release {r['discogs_id']}: {e}")
        try:
            conn.close()
        except:
            pass
        conn = get_conn()
        cur = conn.cursor()

cur.close()
conn.close()
print(f"Updated {artist_count} artists and {release_count} releases")