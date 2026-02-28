from flask import Flask, render_template, jsonify, request, json
from models import db, Release, Artist
from dotenv import load_dotenv
load_dotenv()
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///basement_stacks.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def welcome():
    releases = Release.query.join(Artist).order_by(Artist.sort_name, Release.release_year).limit(10).all()
    return render_template('index.html', releases=releases)

@app.route('/api/releases')
def api_releases():
    page = request.args.get('page', 1, type=int)
    sort = request.args.get('sort', 'random')
    per_page = 1200

    query = Release.query.join(Artist)

    if sort == 'az':
        query = query.order_by(Artist.sort_name, Release.release_year, Release.sort_order)
    else:
        query = query.order_by(db.func.random())

    releases = query.paginate(page=page, per_page=per_page, error_out=False)

    data = [{
        'id': r.id,
        'title': r.title,
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

    if not query:
        return jsonify({'releases': []})

    #Detect if query is a year or decade
    if query.isdigit() and len(query) == 4:
        releases = Release.query.join(Artist).filter(
            Release.release_year == int(query)
        ).order_by(db.func.random()).all()
    elif query.endswith('s') and query[:-1].isdigit():
        decade_str = query[:-1]
        if len(decade_str) == 2:
            decade_start = int('19' + decade_str)
        else:
            decade_start = int(decade_str)
        releases = Release.query.join(Artist).filter(
            Release.release_year >= decade_start,
            Release.release_year < decade_start + 10
        ).order_by(db.func.random()).all()
    else:
        search_term = f'%{query}'
        releases = Release.query.join(Artist).filter(
            db.or_(
                Release.title.ilike(search_term),
                Artist.name.ilike(search_term)
            )
        ).order_by(Artist.sort_name, Release.release_year).all()

        #Also search tracklists
        tracklist_matches = Release.query.join(Artist).filter(
            Release.tracklist.isnot(None)
        ).order_by(Artist.sort_name, Release.release_year, Release.sort_order).all()

        for release in tracklist_matches:
            if release not in releases:
                try:
                    tracks = json.loads(release.tracklist)
                    for track in tracks:
                        if query.lower() in track.get('title', '').lower():
                            releases.append(release)
                            break
                except:
                    pass
        
    data = [{
        'id': r.id,
        'title': r.title,
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

if __name__ == '__main__':
    app.run(debug=True)
