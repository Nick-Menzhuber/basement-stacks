from flask import Flask, render_template
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
    releases = Release.query.join(Artist).order_by(Artist.sort_name, Release.release_year).limit(30).all()
    return render_template('index.html', releases=releases)

if __name__ == '__main__':
    app.run(debug=True)
