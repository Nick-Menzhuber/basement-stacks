from flask import Flask, render_template, jsonify, request
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

if __name__ == '__main__':
    app.run(debug=True)
