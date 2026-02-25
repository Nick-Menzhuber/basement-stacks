from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sort_name = db.Column(db.String(200), nullable=False)
    is_various_artists = db.Column(db.Boolean, default=False)
    discogs_artist_id = db.Column(db.String(50))
    bio = db.Column(db.Text)
    birthday = db.Column(db.Date)

class Membership(db.Model):
    __tablename__ = 'memberships'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    group_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)

    artist = db.relationship('Artist', foreign_keys=[artist_id], backref=db.backref('group_memberships', lazy=True))
    group = db.relationship('Artist', foreign_keys=[group_id], backref=db.backref('members', lazy=True))

class Release(db.Model):
    __tablename__ = 'releases'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artists.id'), nullable=False)
    release_year = db.Column(db.Integer, nullable=True)
    release_date = db.Column(db.Date, nullable=True)
    sort_order = db.Column(db.Integer)
    discogs_id = db.Column(db.String(50))
    master_id = db.Column(db.String(50))
    tracklist = db.Column(db.Text)
    cover_image_url = db.Column(db.String(500))
    custom_cover_image_url = db.Column(db.String(500))
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