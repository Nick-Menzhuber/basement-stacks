from flask import render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os
from admin import admin_bp

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated

@admin_bp.route('/')
@login_required
def index():
    return render_template('admin/index.html')

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form.get('password') == os.environ.get('ADMIN_PASSWORD'):
            session['admin_logged_in'] = True
            return redirect(url_for('admin.index'))
        error = 'Incorrect password'
    return render_template('admin/login.html', error=error)

@admin_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('admin.login'))

from models import db, Release, Artist, Format

@admin_bp.route('/releases')
@login_required
def releases():
    return render_template('admin/releases.html')

@admin_bp.route('/api/search/releases')
@login_required
def search_releases():
    id = request.args.get('id', None)
    if id:
        r = db.get_or_404(Release, int(id))
        results = [r]
    else:
        q = request.args.get('q', '').strip()
        if not q:
            return jsonify([])
        results = Release.query.join(Artist).filter(
            db.or_(
                Release.title.ilike(f'%{q}%'),
                Artist.name.ilike(f'%{q}%')
            )
        ).order_by(Artist.sort_name, Release.release_year).limit(20).all()

    return jsonify([{
        'id': r.id,
        'title': r.title,
        'short_title': r.short_title,
        'artist': r.artist.name,
        'release_year': r.release_year,
        'format_override': r.format_override,
        'sort_title': r.sort_title,
        'sort_order': r.sort_order,
        'mood': r.mood,
        'notes': r.notes,
        'hidden': r.hidden,
        'is_customized': r.is_customized,
        'custom_cover_image_url': r.custom_cover_image_url,
        'cover_image_url': r.cover_image_url,
        'formats': [f.format_name for f in r.formats]
    } for r in results])

@admin_bp.route('/api/releases/<int:id>', methods=['PATCH'])
@login_required
def update_release(id):
    release = db.get_or_404(Release, id)
    data = request.get_json()
    
    fields = ['short_title', 'sort_title', 'sort_order', 'format_override',
              'mood', 'notes', 'hidden', 'is_customized', 'custom_cover_image_url']
    
    for field in fields:
        if field in data:
            setattr(release, field, data[field])
    
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/artists')
@login_required
def artists():
    return render_template('admin/artists.html')

@admin_bp.route('/api/search/artists')
@login_required
def search_artists():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    
    results = Artist.query.filter(
        db.or_(
            Artist.name.ilike(f'%{q}%'),
            Artist.sort_name.ilike(f'%{q}%')
        )
    ).order_by(Artist.sort_name).limit(20).all()
    
    return jsonify([{
        'id': a.id,
        'name': a.name,
        'display_name': a.display_name,
        'sort_name': a.sort_name,
        'birthday': a.birthday.isoformat() if a.birthday else None,
        'image_url': a.image_url,
        'custom_profile': a.custom_profile,
        'hidden': a.hidden or False,
        'is_various_artists': a.is_various_artists or False,
        'primary_artist_id': a.primary_artist_id,
        'primary_artist_name': a.primary_artist.name if a.primary_artist else None
    } for a in results])

@admin_bp.route('/api/artists/<int:id>', methods=['PATCH'])
@login_required
def update_artist(id):
    artist = db.get_or_404(Artist, id)
    data = request.get_json()
    
    fields = ['display_name', 'sort_name', 'custom_profile', 'birthday',
              'image_url', 'hidden', 'is_various_artists', 'primary_artist_id']
    
    for field in fields:
        if field in data:
            setattr(artist, field, data[field])
    
    db.session.commit()
    return jsonify({'success': True})

@admin_bp.route('/queue')
@login_required
def queue():
    total = Release.query.filter(
        Release.is_customized == False,
        Release.hidden == False
    ).count()
    
    releases = Release.query.join(Artist).filter(
        Release.is_customized == False,
        Release.hidden == False
    ).order_by(Release.date_added.desc()).limit(50).all()
    
    return render_template('admin/queue.html', releases=releases, total=total)