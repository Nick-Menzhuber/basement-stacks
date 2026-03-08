from flask import Flask, render_template, jsonify, request, json
from models import db, Release, Artist, Format
from dotenv import load_dotenv
load_dotenv()
import os
import json
import unicodedata

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///basement_stacks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

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

    query = Release.query.join(Artist)
    
    if format_filter != 'all':
        query = query.join(Format).filter(Format.format_name == format_filter)

    if sort == 'az':
        query = query.order_by(Artist.sort_name, Release.release_year, Release.sort_order)
    else:
        query = query.order_by(db.func.random())

    releases = query.paginate(page=page, per_page=per_page, error_out=False)

    data = [{
        'id': r.id,
        'title': r.title,
        'artist_id': r.artist.id,
        'artist': r.artist.name,
        'cover_image_url': r.cover_image_url,
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
        if query.isdigit() and len(query) == 4:
            q = Release.query.join(Artist)
            if format_filter != 'all':
                q = q.join(Format).filter(Format.format_name == format_filter)
            releases = q.filter(
                Release.release_year == int(query)
            ).order_by(db.func.random()).all()
        elif query.endswith('s') and query[:-1].isdigit():
            decade_str = query[:-1]
            if len(decade_str) == 2:
                decade_start = int('19' + decade_str)
            else:
                decade_start = int(decade_str)
                if format_filter != 'all':
                    q = q.join(Format).filter(Format.format_name == format_filter)
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
        releases = q.order_by(Artist.sort_name, Release.release_year, Release.sort_order).all()

    data = [{
        'id': r.id,
        'title': r.title,
        'artist_id': r.artist.id,
        'artist': r.artist.name,
        'cover_image_url': r.cover_image_url,
        'release_year': r.release_year,
        'formats': [f.format_name for f in r.formats]
    } for r in releases]

    return jsonify({'releases': data})

@app.route('/release/<int:id>')
def release_detail(id):
    release = db.get_or_404(Release, id)
    tracklist = json.loads(release.tracklist) if release.tracklist else []
    return render_template('release.html', release=release, tracklist=tracklist)

@app.route('/artist/<int:id>')
def artist_detail(id):
    artist = db.get_or_404(Artist, id)
    releases = Release.query.filter_by(artist_id=artist.id).order_by(Release.release_year, Release.sort_order).all()
    return render_template('artist.html', artist=artist, releases=releases)

if __name__ == '__main__':
    app.run(debug=True)
