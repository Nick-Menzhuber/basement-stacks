from flask import Flask, render_template, jsonify, request, json
from sqlalchemy import case
from models import db, Release, Artist, Format, ArtistAppearance, Membership
from dotenv import load_dotenv
load_dotenv()
import os
import re
import json
import unicodedata

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-prod')
db_url = os.environ.get('DATABASE_URL', 'postgresql://localhost/basement_stacks')
db_url = re.sub(r'^postgres://', 'postgresql://', db_url)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

from flask_migrate import Migrate
migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

from admin import admin_bp
app.register_blueprint(admin_bp)
    

def normalize_search(text):
    if not text:
        return None
    return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii').lower()

@app.template_filter('from_json')
def from_json_filter(value):
    try:
        return json.loads(value)
    except:
        return []

@app.route('/')
def welcome():
    releases = Release.query.join(Artist).order_by(Artist.sort_name, Release.release_year).limit(10).all()
    return render_template('index.html', releases=releases)

@app.route('/api/releases')
def api_releases():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'az')
    format_filter = request.args.get('format', 'all')
    per_page = 30

    query = Release.query.join(Artist).filter(Release.hidden == False, Artist.hidden == False)
    
    if format_filter != 'all':
        query = query.join(Format).filter(Format.format_name == format_filter)

    if sort == 'az':
        sort_key = case(
            (Artist.is_various_artists == True, db.func.coalesce(Release.sort_title, Release.title)),
            else_=Artist.sort_name
        )
        query = query.order_by(sort_key, Release.release_year, Release.sort_order)
    else:
        query = query.order_by(db.func.random())

    releases = query.paginate(page=page, per_page=per_page, error_out=False)

    data = [{
        'id': r.id,
        'title': r.title,
        'short_title': r.short_title,
        'artist_id': r.artist.id,
        'artist': r.artist.name,
        'sort_name': r.artist.sort_name,
        'cover_image_url': r.cover_image_url,
        'custom_cover_image_url': r.custom_cover_image_url,
        'release_year': r.release_year,
        'formats': [f.format_name for f in r.formats]
    } for r in releases.items]

    return jsonify({
        'releases': data,
        'has_next': releases.has_next,
        'page': page
    })

@app.route('/api/search')
def api_search():
    query = request.args.get('q', '').strip()
    scope = request.args.get('scope', 'albums')
    format_filter = request.args.get('format', 'all')

    if not query:
        return jsonify({'releases': []})

    if scope == 'years':
        q = Release.query.join(Artist)
        if format_filter != 'all':
            q = q.join(Format).filter(Format.format_name == format_filter)
    
        if query.isdigit() and len(query) == 4:
            releases = q.filter(
                Release.release_year == int(query)
            ).order_by(db.func.random()).all()
        elif query.endswith('s') and query[:-1].isdigit():
            decade_str = query[:-1]
            if len(decade_str) == 2:
                decade_start = int('19' + decade_str)
            else:
                decade_start = int(decade_str)
            releases = q.filter(
                Release.release_year >= decade_start,
                Release.release_year < decade_start + 10
            ).order_by(db.func.random()).all()
        else:
            releases = []

    elif scope == 'songs':
        releases = []
        q = Release.query.join(Artist).filter(Release.tracklist.isnot(None))
        if format_filter != 'all':
            q = q.join(Format).filter(Format.format_name == format_filter)
        tracklist_matches = q.order_by(Artist.sort_name, Release.release_year).all()
        for release in tracklist_matches:
            try:
                tracks = json.loads(release.tracklist)
                for track in tracks:
                    if query.lower() in track.get('title', '').lower():
                        releases.append(release)
                        break
            except:
                pass

    else:  # albums scope
        normalized_query = normalize_search(query)
        search_term = f'%{query}%'
        normalized_term = f'%{normalized_query}%'
        q = Release.query.join(Artist).filter(
            db.or_(
                Release.title.ilike(search_term),
                Artist.name.ilike(search_term),
                Artist.search_name.ilike(normalized_term)
            )
        )
        if format_filter != 'all':
            q = q.join(Format).filter(Format.format_name == format_filter)
        releases = q.order_by(
            case(
                (Artist.is_various_artists == True, db.func.coalesce(Release.sort_title, Release.title)),
                else_=Artist.sort_name
            ),
            Release.release_year, Release.sort_order
        ).all()

    data = [{
        'id': r.id,
        'title': r.title,
        'short_title': r.short_title,
        'artist_id': r.artist.id,
        'artist': r.artist.name,
        'cover_image_url': r.cover_image_url,
        'custom_cover_image_url': r.custom_cover_image_url,
        'release_year': r.release_year,
        'formats': [f.format_name for f in r.formats]
    } for r in releases]

    return jsonify({'releases': data})

@app.route('/release/<int:id>')
def release_detail(id):
    release = db.get_or_404(Release, id)
    if len(release.formats) == 1 and release.individual_tracklist:
        tracklist = json.loads(release.individual_tracklist)
    else:
        tracklist = json.loads(release.tracklist) if release.tracklist else []
    return render_template('release.html', release=release, tracklist=tracklist)

@app.route('/artist/<int:id>')
def artist_detail(id):
    artist = db.get_or_404(Artist, id)
    
    artist_ids = [artist.id] + [a.id for a in artist.aliases]
    
    releases = Release.query.filter(
        Release.artist_id.in_(artist_ids)
    ).order_by(Release.release_year, Release.sort_order).all()
    
    appearances = ArtistAppearance.query.filter_by(artist_id=artist.id).all()
    
    def member_has_collection_overlap(member_artist, group_id):
        """Check if member was in the band during years we have releases for that band"""
        membership = Membership.query.filter_by(artist_id=member_artist.id, group_id=group_id).first()
        
        if not membership:
            return False
        
        # If no dates at all, include them (Discogs-only membership, no MB data)
        if not membership.begin_date and not membership.end_date:
            return True
        
        # Get the band's releases in collection
        band_releases = Release.query.filter_by(artist_id=group_id, hidden=False).all()
        
        for r in band_releases:
            if not r.release_year:
                continue
            year = r.release_year
            begin_year = membership.begin_date.year if membership.begin_date else None
            end_year = membership.end_date.year if membership.end_date else None
            
            if begin_year and year >= begin_year and (not end_year or year <= end_year):
                return True
        
        return False

    member_groups = Artist.query.join(
        Membership, Membership.group_id == Artist.id
    ).join(
        Release, Release.artist_id == Artist.id
    ).filter(
        Membership.artist_id == artist.id
    ).distinct().all()
    
    # Filter to only groups where artist has collection overlap
    member_groups = [g for g in member_groups if member_has_collection_overlap(artist, g.id)]

    # ... rest continues as before

    # Add collaboration releases as appearances
    collab_releases = Release.query.join(Artist).filter(
        Release.artist_id.in_([g.id for g in member_groups]),
        Release.hidden == False
    ).all() if member_groups else []

    appearance_releases = sorted(
        [a.release for a in appearances] + collab_releases,
        key=lambda r: r.release_year or 0
    )

    # Collaboration members and their releases
    members = []
    member_releases = []
    if artist.members:
        members = [
            m.artist for m in artist.members 
            if member_has_collection_overlap(m.artist, artist.id) and not m.artist.hidden
        ]

        seen = set()
        for member in members:
            for r in Release.query.filter_by(artist_id=member.id).filter(Release.hidden == False).order_by(Release.release_year).all():
                if r.id not in seen:
                    seen.add(r.id)
                    member_releases.append((member, r))
    
    return render_template('artist.html', artist=artist, releases=releases, 
                         appearance_releases=appearance_releases, 
                         member_groups=member_groups,
                         members=members,
                         member_releases=member_releases)

@app.route('/release/<int:id>/<format_slug>')
def release_detail_format(id, format_slug):
    format_map = {
        'vinyl': 'Vinyl',
        'cd': 'CD',
        'cassette': 'Cassette',
        '7inch': '7"'
    }
    format_name = format_map.get(format_slug)
    release = db.get_or_404(Release, id)
    
    fmt = Format.query.filter_by(
        release_id=release.id,
        format_name=format_name
    ).first_or_404()

    # Fetch the format-specific tracklist from Discogs
    tracklist = []
    if fmt.discogs_release_id:
        import requests
        token = os.getenv('DISCOGS_TOKEN')
        headers = {
            'Authorization': f'Discogs token={token}',
            'User-Agent': 'BasementStacks/1.0'
        }
        url = f'https://api.discogs.com/releases/{fmt.discogs_release_id}'
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            data = response.json()
            tracklist = data.get('tracklist', [])
    
    return render_template('release.html', release=release, tracklist=tracklist, active_format=format_name)

@app.route('/api/releases/count')
def api_releases_count():
    total = Release.query.filter(Release.hidden == False).count()
    per_page = 30
    total_pages = (total + per_page - 1) // per_page
    return jsonify({'total_pages': total_pages})

@app.route('/api/releases/letters')
def api_releases_letters():
    format_filter = request.args.get('format', 'all')
    
    query = Release.query.join(Artist).filter(
        Release.hidden == False,
        Artist.hidden == False
    )
    
    if format_filter != 'all':
        query = query.join(Format).filter(Format.format_name == format_filter)
    
    results = query.with_entities(
        Artist.sort_name,
        Artist.is_various_artists,
        Release.sort_title,
        Release.title
    ).all()

    letter_counts = {}
    for r in results:
        if r.is_various_artists:
            sort_name = r.sort_title or r.title or ''
        else:
            sort_name = r.sort_name or ''
        first_char = sort_name[0].upper() if sort_name else '#'
        letter = '#' if first_char.isdigit() else first_char
        letter_counts[letter] = letter_counts.get(letter, 0) + 1
    
    letter_list = sorted(letter_counts.keys(), key=lambda x: (x != '#', x))
    substantial = [k for k, v in letter_counts.items() if v >= 30]
    
    return jsonify({
        'letters': letter_list,
        'substantial': substantial
    })

@app.route('/api/releases/by-letter')
def api_releases_by_letter():
    format_filter = request.args.get('format', 'all')
    letter = request.args.get('letter', None)

    sort_key = case(
        (Artist.is_various_artists == True, db.func.coalesce(Release.sort_title, Release.title)),
        else_=Artist.sort_name
    )

    query = Release.query.join(Artist).filter(
        Release.hidden == False,
        Artist.hidden == False
    )

    if format_filter != 'all':
        query = query.join(Format).filter(Format.format_name == format_filter)

    query = query.order_by(sort_key, Release.release_year, Release.sort_order)

    if letter:
        if letter == '#':
            query = query.filter(
                db.func.left(sort_key, 1).in_(
                    [str(i) for i in range(10)]
                )
            )
        else:
            query = query.filter(
                db.func.upper(db.func.left(sort_key, 1)) == letter
            )
        
    releases = query.all()
    
    data = [{
        'id': r.id,
        'title': r.title,
        'short_title': r.short_title,
        'artist_id': r.artist.id,
        'artist': r.artist.name,
        'sort_name': r.artist.sort_name,
        'cover_image_url': r.cover_image_url,
        'custom_cover_image_url': r.custom_cover_image_url,
        'release_year': r.release_year,
        'formats': [f.format_name for f in r.formats]
    } for r in releases]
    
    return jsonify({'releases': data})

if __name__ == '__main__':
    app.run(debug=True)
