#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import date

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class City(db.Model):
    __tablename__ = 'city'
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    venues = db.relationship('Venue', backref='city', lazy=True)
    artists = db.relationship('Artist', backref='city', lazy=True)
    def __repr__(self):
        return f'<City {self.id} {self.city}>'

class Venue(db.Model):
    __tablename__ = 'venue'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String(120), nullable=False)
    cityid = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    seeking_talent = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show', backref='venue', lazy=True)
    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'

class Artist(db.Model):
    __tablename__ = 'artist'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    cityid = db.Column(db.Integer, db.ForeignKey('city.id'), nullable=False)
    phone = db.Column(db.String(120))
    website = db.Column(db.String(120))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.String(500))
    seeking_venue = db.Column(db.Boolean(), default=False)
    seeking_description = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    shows = db.relationship('Show', backref='artist', lazy=True)
    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'

class Show(db.Model):
    __tablename__ = 'show'
    id = db.Column(db.Integer, primary_key=True)
    artistid = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    venueid = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    def __repr__(self):
        return f'<Show {self.id} {self.start_time}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  if isinstance(value, str):
      date = dateutil.parser.parse(value)
  else:
      date = value
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime


#----------------------------------------------------------------------------#
# Get City Id.
#----------------------------------------------------------------------------#

def get_city(city_name, state_code):
    # Check db for existing city, state
    city = City.query.filter_by(city=city_name, state=state_code)
    if city.count(): # Check if city already exists
        return city[0].id
    else: # Else create new city entry in db
        city_id = ''
        new_city = City(city=city_name, state=state_code)
        db.session.add(new_city)
        db.session.flush()
        city_id = new_city.id
        return city_id

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_shows should be aggregated based on number of upcoming shows per venue.
  cities = City.query.all();
  data=[]
  for city in cities:
      citydata = {
        "city": city.city,
        "state": city.state,
        "venues": Venue.query.filter_by(cityid=city.id).all()
      }
      data.append(citydata)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  response={
    "count": 1,
    "data": [{
      "id": 2,
      "name": "The Dueling Pianos Bar",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).all()[0]
    today = date.today()
    # Upcoming shows
    upcoming_shows = Show.query.filter(Show.venueid == venue.id, Show.start_time > today).all()
    shows_upcoming = []
    for upcoming_show in upcoming_shows:
        show = {
            "artist_id": upcoming_show.artist.id,
            "artist_name": upcoming_show.artist.name,
            "artist_image_link": upcoming_show.artist.image_link,
            "start_time": upcoming_show.start_time
        }
        shows_upcoming.append(show)
    # EO Upcoming shows
    # Past shows
    past_shows = Show.query.filter(Show.venueid == venue.id, Show.start_time <= today).all()
    shows_past = []
    for past_show in past_shows:
        show = {
            "artist_id": past_show.artist.id,
            "artist_name": past_show.artist.name,
            "artist_image_link": past_show.artist.image_link,
            "start_time": past_show.start_time
        }
        shows_past.append(show)
    # EO Past shows
    # Generate genre list
    genres = []
    if isinstance(venue.genres, str):
        genres = venue.genres.split(',')
    # EO Generate genre list
    data = {
      "id": venue.id,
      "name": venue.name,
      "address": venue.address,
      "city": venue.city.city,
      "state": venue.city.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "genres": genres,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": shows_past,
      "upcoming_shows": shows_upcoming,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Check db for submitted city, state
    city_name = request.form.get('city')
    state_code = request.form.get('state')
    cityid = get_city(city_name, state_code)
    # EO Check db for submitted city, state
    # Generate genre list
    genres = request.form.getlist('genres') # Fetch list from form
    genres =  ",".join(genres) # Convert to comma separated string to store in db
    # EO Generate genre list
    venue = Venue(
        name=request.form.get('name'),
        address=request.form.get('address'),
        cityid=cityid,
        phone=request.form.get('phone'),
        website=request.form.get('website_link'),
        genres=genres,
        facebook_link=request.form.get('facebook_link'),
        seeking_talent=bool(request.form.get('seeking_talent')), # bool() to convert into boolean SQLAlchemy likes...
        seeking_description=request.form.get('seeking_description'),
        image_link=request.form.get('image_link')
    )
    error = False
    try:
        db.session.add(venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
        return render_template('pages/home.html')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  response={
    "count": 1,
    "data": [{
      "id": 4,
      "name": "Guns N Petals",
      "num_upcoming_shows": 0,
    }]
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.filter_by(id=artist_id).all()[0]
    today = date.today()
    # Upcoming shows
    upcoming_shows = Show.query.filter(Show.artistid == artist.id, Show.start_time > today).all()
    shows_upcoming = []
    for upcoming_show in upcoming_shows:
        show = {
            "venue_id": upcoming_show.venue.id,
            "venue_name": upcoming_show.venue.name,
            "venue_image_link": upcoming_show.venue.image_link,
            "start_time": upcoming_show.start_time
        }
        shows_upcoming.append(show)
    # EO Upcoming shows
    # Past shows
    past_shows = Show.query.filter(Show.artistid == artist.id, Show.start_time <= today).all()
    shows_past = []
    for past_show in past_shows:
        show = {
            "venue_id": past_show.venue.id,
            "venue_name": past_show.venue.name,
            "venue_image_link": past_show.venue.image_link,
            "start_time": past_show.start_time
        }
        shows_past.append(show)
    # EO Past shows
    # Generate genre list
    genres = []
    if isinstance(artist.genres, str):
        genres = artist.genres.split(',')
    # EO Generate genre list
    data = {
      "id": artist.id,
      "name": artist.name,
      "city": artist.city.city,
      "state": artist.city.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "genres": genres,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": shows_past,
      "upcoming_shows": shows_upcoming,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows)
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.filter_by(id=artist_id).all()[0]
  form = ArtistForm()
  # Populate form with db data
  form.name.data = artist.name
  form.city.data = artist.city.city
  form.state.data = artist.city.state
  form.phone.data = artist.phone
  form.website_link.data = artist.website
  form.facebook_link.data = artist.facebook_link
  form.genres.data = artist.genres
  form.seeking_venue.data = artist.seeking_venue
  form.seeking_description.data = artist.seeking_description
  form.image_link.data = artist.image_link
  # EO Populate form with db data
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    artist = Artist.query.get(artist_id)
    error = False
    # Generate genre list
    genres = request.form.getlist('genres') # Fetch list from form
    genres =  ",".join(genres) # Convert to comma separated string to store in db
    # EO Generate genre list
    try:
        # Check db for submitted city, state
        city_name = request.form.get('city')
        state_code = request.form.get('state')
        cityid = get_city(city_name, state_code)
        # EO Check db for submitted city, state
        # Update fields
        artist.name = request.form.get('name')
        artist.cityid = cityid
        artist.phone = request.form.get('phone')
        artist.website = request.form.get('website_link')
        artist.genres = genres
        artist.facebook_link = request.form.get('facebook_link')
        artist.seeking_venue = bool(request.form.get('seeking_venue')) # bool() to convert into boolean SQLAlchemy likes...
        artist.seeking_description = request.form.get('seeking_description')
        artist.image_link = request.form.get('image_link')
        # EO Update fields
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist could not be uppdated.')
        return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        flash('Artist was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.filter_by(id=venue_id).all()[0]
    form = VenueForm()
    # Populate form with db data
    form.name.data = venue.name
    form.address.data = venue.address
    form.city.data = venue.city.city
    form.state.data = venue.city.state
    form.phone.data = venue.phone
    form.website_link.data = venue.website
    form.facebook_link.data = venue.facebook_link
    form.genres.data = venue.genres
    form.seeking_talent.data = venue.seeking_talent
    form.seeking_description.data = venue.seeking_description
    form.image_link.data = venue.image_link
    # EO Populate form with db data
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    venue = Venue.query.get(venue_id)
    error = False
    # Generate genre list
    genres = request.form.getlist('genres') # Fetch list from form
    genres =  ",".join(genres) # Convert to comma separated string to store in db
    # EO Generate genre list
    try:
        # Check db for submitted city, state
        city_name = request.form.get('city')
        state_code = request.form.get('state')
        cityid = get_city(city_name, state_code)
        # EO Check db for submitted city, state
        # Update fields
        venue.name = request.form.get('name')
        venue.address = request.form.get('address')
        venue.cityid = cityid
        venue.phone = request.form.get('phone')
        venue.website = request.form.get('website_link')
        venue.facebook_link = request.form.get('facebook_link')
        venue.genres = genres
        venue.seeking_talent = bool(request.form.get('seeking_talent')) # bool() to convert into boolean SQLAlchemy likes...
        venue.seeking_description = request.form.get('seeking_description')
        venue.image_link = request.form.get('image_link')
        # EO Update fields
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Venue could not be updated.')
        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        flash('Venue was successfully updated!')
        return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # Check db for submitted city, state
    city_name = request.form.get('city')
    state_code = request.form.get('state')
    cityid = get_city(city_name, state_code)
    # EO Check db for submitted city, state
    # Generate genre list
    genres = request.form.getlist('genres') # Fetch list from form
    genres =  ",".join(genres) # Convert to comma separated string to store in db
    # EO Generate genre list
    artist = Artist(
        name=request.form.get('name'),
        cityid=cityid,
        phone=request.form.get('phone'),
        website=request.form.get('website_link'),
        facebook_link=request.form.get('facebook_link'),
        genres=genres,
        seeking_venue=bool(request.form.get('seeking_venue')), # bool() to convert into boolean SQLAlchemy likes...
        seeking_description=request.form.get('seeking_description'),
        image_link=request.form.get('image_link')
    )
    error = False
    try:
        db.session.add(artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
        return render_template('pages/home.html')
    else:
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = []
    today = date.today()
    shows = Show.query.filter(Show.start_time>today).all()
    for show in shows:
        show = {
            "venue_id": show.venue.id,
            "venue_name": show.venue.name,
            "artist_id": show.artistid,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time
        }
        data.append(show)
    return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    show = Show(
        artistid=request.form.get('artist_id'),
        venueid=request.form.get('venue_id'),
        start_time=request.form.get('start_time')
    )
    error = False
    try:
        db.session.add(show)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
    finally:
        db.session.close()
    if error:
        flash('An error occurred. Show could not be listed.')
        return render_template('pages/home.html')
    else:
        flash('Show was successfully listed!')
        return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
