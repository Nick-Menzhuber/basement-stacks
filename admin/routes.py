from flask import render_template, request, redirect, url_for, session, jsonify
from functools import wraps
import os, time
from admin import admin_bp
from models import db, Release, Artist, Format, Membership

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
        'discogs_artist_id': a.discogs_artist_id,
        'musicbrainz_id': a.musicbrainz_id,
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

import requests as http_requests

@admin_bp.route('/api/artists/<int:id>/fetch-discogs', methods=['POST'])
@login_required
def fetch_artist_discogs(id):
    artist = db.get_or_404(Artist, id)
    
    if not artist.discogs_artist_id:
        return jsonify({'error': 'No Discogs artist ID set'}), 400
    
    token = os.environ.get('DISCOGS_TOKEN')
    headers = {
        'Authorization': f'Discogs token={token}',
        'User-Agent': 'BasementStacks/1.0'
    }
    
    url = f'https://api.discogs.com/artists/{artist.discogs_artist_id}'
    response = http_requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return jsonify({'error': f'Discogs returned {response.status_code}'}), 500
    
    data = response.json()
    
    # Only update fields that are empty
    if not artist.image_url and data.get('images'):
        artist.image_url = data['images'][0].get('uri')
    if not artist.profile and data.get('profile'):
        artist.profile = data['profile']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'image_url': artist.image_url,
        'profile': artist.profile
    })

import time

@admin_bp.route('/api/artists/<int:id>/fetch-musicbrainz', methods=['POST'])
@login_required
def fetch_artist_musicbrainz(id):
    artist = db.get_or_404(Artist, id)
    from datetime import date
    
    headers = {
        'User-Agent': 'BasementStacks/1.0 (nickmenzhuber@gmail.com)'
    }
    
    # Step 1: Find or confirm MBID
    if artist.musicbrainz_id:
        mbid = artist.musicbrainz_id
    else:
        response = http_requests.get(
            'https://musicbrainz.org/ws/2/artist',
            headers=headers,
            params={'query': f'artist:"{artist.name}"', 'fmt': 'json', 'limit': 5}
        )
        candidates = response.json().get('artists', [])
        if not candidates:
            return jsonify({'error': 'No MusicBrainz matches found', 'candidates': []})
        
        if len(candidates) == 1 or candidates[0]['score'] == 100:
            mbid = candidates[0]['id']
            artist.musicbrainz_id = mbid
            db.session.commit()
        else:
            return jsonify({
                'needs_selection': True,
                'candidates': [{
                    'id': c['id'],
                    'name': c['name'],
                    'disambiguation': c.get('disambiguation', ''),
                    'country': c.get('country', ''),
                    'score': c['score']
                } for c in candidates]
            })
    
    # Step 2: Fetch artist relationships
    time.sleep(1)
    response = http_requests.get(
        f'https://musicbrainz.org/ws/2/artist/{mbid}',
        headers=headers,
        params={'inc': 'artist-rels', 'fmt': 'json'}
    )
    data = response.json()
    
    # Helper to parse partial dates
    def parse_mb_date(date_str):
        if not date_str:
            return None
        parts = date_str.split('-')
        try:
            year = int(parts[0])
            month = int(parts[1]) if len(parts) > 1 else 1
            day = int(parts[2]) if len(parts) > 2 else 1
            return date(year, month, day)
        except (ValueError, IndexError):
            return None
    
    # Step 3: MusicBrainz is now source of truth for membership
    members_updated = 0
    mb_member_mbrids = set()
    
    for rel in data.get('relations', []):
        if rel.get('type') == 'member of band' and rel.get('direction') == 'backward':
            member_name = rel['artist']['name']
            member_mbid = rel['artist']['id']
            begin = rel.get('begin')
            end = rel.get('end')
            is_current = not rel.get('ended', False)
            
            mb_member_mbrids.add(member_mbid)
            
            # Find or create member artist
            member = Artist.query.filter(
                db.or_(
                    Artist.musicbrainz_id == member_mbid,
                    Artist.name == member_name
                )
            ).first()
            
            if not member:
                # Create new artist with just name + MBID
                member = Artist(
                    name=member_name,
                    sort_name=member_name,
                    musicbrainz_id=member_mbid,
                    hidden=False
                )
                db.session.add(member)
                db.session.flush()
            else:
                if not member.musicbrainz_id:
                    member.musicbrainz_id = member_mbid
            
            # Find or create membership
            membership = Membership.query.filter_by(
                artist_id=member.id,
                group_id=artist.id
            ).first()
            
            if not membership:
                membership = Membership(
                    artist_id=member.id,
                    group_id=artist.id
                )
                db.session.add(membership)
            
            # Update dates from MB
            new_begin = parse_mb_date(begin)
            new_end = parse_mb_date(end)
            
            # Take earliest begin and latest end (handles rejoining members)
            if new_begin and (not membership.begin_date or new_begin < membership.begin_date):
                membership.begin_date = new_begin
            if new_end and (not membership.end_date or new_end > membership.end_date):
                membership.end_date = new_end
            membership.is_current = is_current
            members_updated += 1
    
    # Identify orphaned memberships (in our DB but not in MB)
    orphaned = []
    for m in Membership.query.filter_by(group_id=artist.id).all():
        if m.artist.musicbrainz_id and m.artist.musicbrainz_id not in mb_member_mbrids:
            orphaned.append(m.artist.name)
       
    try:
        db.session.commit()
    except Exception as e:
        print(f"MB fetch commit failed: {e}")
        db.session.rollback()
        return jsonify({'error': 'Database commit failed'}), 500

    return jsonify({
        'success': True,
        'mbid': mbid,
        'members_updated': members_updated,
        'members_orphaned': len(orphaned),
        'orphaned_names': orphaned,
        'name': data.get('name')
    })

@admin_bp.route('/api/artists/<int:id>/set-musicbrainz', methods=['POST'])
@login_required
def set_artist_musicbrainz(id):
    artist = db.get_or_404(Artist, id)
    data = request.get_json()
    mbid = data.get('mbid')
    if not mbid:
        return jsonify({'error': 'No MBID provided'}), 400
    artist.musicbrainz_id = mbid
    db.session.commit()
    return jsonify({'success': True, 'mbid': mbid})