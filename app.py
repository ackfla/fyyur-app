#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for,
    abort
)
from flask_moment import Moment
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import date
from models import db, City, Venue, Artist, Show

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app) # Init db
migrate = Migrate(app, db)

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
  cities = City.query.all();
  data=[]
  today = date.today()
  for city in cities:
      citydata = {
        "city": city.city,
        "state": city.state,
        "venues": []
      }
      venues = Venue.query.filter_by(cityid=city.id).all()
      for venue in venues:
          venue = {
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": Show.query.filter(Show.venueid==venue.id, Show.start_time>today).count()
          }
          citydata['venues'].append(venue)
      data.append(citydata)

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = '%' + request.form.get('search_term') + '%'
    results = Venue.query.filter(Venue.name.ilike(search_term)).all() # Use ilike query as case insensitive
    response={
      "count": len(results),
      "data": []
    }
    for result in results:
        artist = {
          "id": result.id,
          "name": result.name
        }
        response['data'].append(artist)
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    past_shows = []
    upcoming_shows = []
    venue = Venue.query.get_or_404(venue_id) # Get current venue
    today = date.today() # Get current date

    # Loop over shows
    for show in venue.shows:
        temp_show = {
            "artist_id": show.artist.id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": show.start_time
        }
        # Filter into correct list by date
        if show.start_time.date() > today:
            upcoming_shows.append(temp_show)
        else:
            past_shows.append(temp_show)

    # object class to dict
    data = vars(venue)

    # Add city data
    city = venue.city
    data['city'] = city.city
    data['state'] = city.state

    # Add genres in correct format
    genres = []
    if isinstance(venue.genres, str):
        genres = venue.genres.split(',')
    data['genres'] = genres

    # Add extra shows data
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    # Get form object
    form = VenueForm(request.form)

    # Check form validation
    if form.validate():
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

    else:
        # On form validation error redirect to back to prefilled form
        return render_template('forms/new_venue.html', form=form)

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  error = False
  try:
      venue = Venue.query.get(venue_id)
      db.session.delete(venue)
      db.session.commit()
  except:
      error = True
      db.session.rollback()
  finally:
      db.session.close()
  if error:
      abort(400)
  else:
      return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = Artist.query.with_entities(Artist.id, Artist.name)
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = '%' + request.form.get('search_term') + '%'
    results = Artist.query.filter(Artist.name.ilike(search_term)).all() # Use ilike query as case insensitive
    response={
      "count": len(results),
      "data": []
    }
    for result in results:
        artist = {
          "id": result.id,
          "name": result.name
        }
        response['data'].append(artist)
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get_or_404(artist_id) # Get current artist
    today = date.today() # Get current date
    past_shows = []
    upcoming_shows = []

    # Loop over shows
    for show in artist.shows:
        temp_show = {
            "venue_id": show.artist.id,
            "venue_name": show.artist.name,
            "venue_image_link": show.artist.image_link,
            "start_time": show.start_time
        }
        # Filter into correct list by date
        if show.start_time.date() > today:
            upcoming_shows.append(temp_show)
        else:
            past_shows.append(temp_show)

    # object class to dict
    data = vars(artist)

    # Add city data
    city = artist.city
    data['city'] = city.city
    data['state'] = city.state

    # Add genres in correct format
    genres = []
    if isinstance(artist.genres, str):
        genres = artist.genres.split(',')
    data['genres'] = genres

    # Add extra shows data
    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)

  form = ArtistForm(obj=artist)

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

    # Get form object
    form = ArtistForm(request.form)
    # Get artist
    artist = Artist.query.get(artist_id)

    # Check form validation
    if form.validate():
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

    else:
        # On form validation error redirect to back to prefilled form
        return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    venue = Venue.query.get_or_404(venue_id)
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

    # Get form object
    form = VenueForm(request.form)
    # Get venue
    venue = Venue.query.get(venue_id)

    # Check form validation
    if form.validate():
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

    else:
        # On form validation error redirect to back to prefilled form
        return render_template('forms/edit_venue.html', form=form, venue=venue)

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    # Get form object
    form = ArtistForm(request.form)

    # Check form validation
    if form.validate():
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
    else:
        # On form validation error redirect to back to prefilled form
        return render_template('forms/new_artist.html', form=form)

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
