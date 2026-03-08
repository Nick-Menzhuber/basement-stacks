from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Artist(db.Model):
    __tablename__ = 'artists'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    sort_name = db.Column(db.String(200), nullable=False)
    search_name = db.Column(db.String(200), nullable=True)
    is_various_artists = db.Column(db.Boolean, default=False)
    discogs_artist_id = db.Column(db.String(50))
    profile = db.Column(db.Text, nullable=True)
    custom_profile = db.Column(db.Text, nullable=True)
    urls = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    videos = db.Column(db.Text, nullable=True)
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
    individual_tracklist = db.Column(db.Text, nullable=True)
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
    discogs_release_id = db.Column(db.String(50), nullable=True)

    release = db.relationship('Release', backref=db.backref('formats', lazy=True))