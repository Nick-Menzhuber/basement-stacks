from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sort_name = db.Column(db.String(200), nullable=False)
    is_various_artists = db.Column(db.Boolean, default=False)

class Release(db.Model):
    __tablename__ = 'releases'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    release_year = db.Column(db.Integer, nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    sort_order = db.Column(db.Integer)
    discogs_id = db.Column(db.String(50))
    cover_image_url = db.Column(db.String(500))
    release_type = db.Column(db.String(50), default='album')
    is_customized = db.Column(db.Boolean, default=False)
    mood = db.Column(db.String(100))
    genre = db.Column(db.String(100))
    date_added = db.Column(db.DateTime)
    notes = db.Column(db.Text)


    artist = db.relationship('Artist', backref=db.backref('releases', lazy=True))

class Format(db.Model):
    __tablename__ = 'formats'

    id = db.Column(db.Integer, primary_key=True)
    release_id = db.Column(db.Integer, db.ForeignKey('releases.id'), nullable=False)
    format_name = db.Column(db.String(50), nullable=False)

    release = db.relationship('Release', backref=db.backref('formats', lazy=True))