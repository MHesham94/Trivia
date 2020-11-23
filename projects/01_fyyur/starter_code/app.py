#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, or_
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import time
import datetime 
import dateutil
from dateutil.parser import parse
from datetime import datetime
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(500))

    # TODO: implement any missing fields, as a database migration using Flask-Migrate

# TODO Implement Show and Artist models, and complete all model relationships and properties, as a database migration.

class Show(db.Model):
	__tablename__ = 'Show'

	id = db.Column(db.Integer, primary_key=True)
	artist_id = db.Column(db.Integer, db.ForeignKey('Artist.id'), nullable=False)
	venue_id = db.Column(db.Integer, db.ForeignKey('Venue.id'), nullable=False)
	start_time = db.Column(db.TIMESTAMP)
	artist = db.relationship('Artist', backref=db.backref('shows', lazy=True))
	venue = db.relationship('Venue', backref=db.backref('shows', lazy=True))

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

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
  data = db.session.query(Venue).group_by(Venue.state, Venue.city)
  locations = db.session.query(Venue.city,Venue.state).distinct(Venue.city,Venue.state).all()
  data = []

  for row in locations:
  	Venues = db.session.query(Venue.id,Venue.name,func.count(Show.id).label('num_shows')).filter_by(state=row.state,city=row.city).outerjoin(Venue.shows).group_by(Venue.id)
  	data.append({"state": row.state,"city":row.city,"venues": Venues})

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  query = request.form.get('search_term', '')
  data = Venue.query.filter(Venue.name.ilike(f'%{query}%')).all()
  current_time = datetime.utcnow()
  search_venue_result = []
  

  for venue in data:
  	count = Show.query.filter_by(venue_id = venue.id).filter(Show.start_time > current_time).count()
  	search_venue_result.append({"id":venue.id,"name": venue.name,"num_shows":count})

  response={
    "count": len(data),
    "data": search_venue_result
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data = db.session.query(Venue).filter_by(id=venue_id).one()
  data.genres = data.genres.replace("{","").replace("}","").split(",")

  current_time = datetime.utcnow()
  pastShows = db.session.query(Artist.id.label('artist_id'),Artist.name.label('artist_name'),Show.start_time.label('start_time'),Artist.image_link.label('artist_image_link')).filter(venue_id == venue_id).filter(Show.start_time < current_time).join(Artist).all()
  data.past_shows = pastShows
  upcomingShows = db.session.query(Artist.id.label('artist_id'),Artist.name.label('artist_name'),Show.start_time.label('start_time'),Artist.image_link.label('artist_image_link')).filter(venue_id == venue_id).filter(Show.start_time > current_time).join(Artist).all()
  data.upcoming_shows = upcomingShows
  data.past_shows_count = len(data.past_shows)
  data.upcoming_shows_count = len(data.upcoming_shows)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
	addVenueForm = VenueForm()
	addVenue = Venue()
	addVenue.name = addVenueForm.name.data
	addVenue.city = addVenueForm.city.data
	addVenue.state = addVenueForm.state.data
	addVenue.address = addVenueForm.address.data
	addVenue.genres = addVenueForm.genres.data
	addVenue.seeking_talent = addVenueForm.seeking_talent.data
	if (addVenue.seeking_talent is True):
		addVenue.seeking_description = addVenueForm.seeking_description.data
	addVenue.website = addVenueForm.website.data
	addVenue.facebook_link = addVenueForm.facebook_link.data
	addVenue.image_link = addVenueForm.image_link.data
	addVenue.phone = addVenueForm.phone.data
	db.session.add(addVenue)
	try:
		db.session.commit()
		flash('Venue ' + addVenueForm.name.data + ' was successfully listed!')
	except Exception as e:
		db.session.rollback()
		db.session.flush()
		flash('An error occurred. Venue'+addvenueForm.name.data+' could not be listed.')
	return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
	db.session.query(Venue).filter_by(id = venue_id).delete()
	try:
		db.session.commit()
		flash('Venue with id '+venue_id +' was successfully deleted!')
	except Exception as e:
		db.session.rollback()
		db.session.flush()
		flash('Error while deleting the venue '+venue_id)
	return render_template('pages/home.html')
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  data = db.session.query(Artist.id,Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
   query = request.form.get('search_term', '')
   data = Artist.query.filter(Artist.name.ilike(f'%{query}%')).all()
   current_time = datetime.utcnow()
   search_artist_result = []
   

   for artist in data:
   	count = Show.query.filter_by(artist_id = artist.id).filter(Show.start_time > current_time).count()
   	search_artist_result.append({"id":artist.id,"name": artist.name,"num_shows":count})

   	response={
    "count": len(data),
    "data": search_artist_result
    }

   return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/shows/search', methods=['POST'])
def search_shows():
   query = request.form.get('search_term', '')
   data = db.session.query(Venue.id.label('venue_id'),Venue.name.label('venue_name'),Artist.id.label('artist_id'),Artist.name.label('artist_name'),Artist.image_link.label('artist_image_link'),Show.start_time.label('start_time')).outerjoin(Venue).outerjoin(Artist).filter(or_(Artist.name.ilike(f'%{query}%'),Venue.name.ilike(f'%{query}%'))).all()

   response={
    "count": len(data),
    "data": data
    }

   return render_template('pages/search_shows.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data = db.session.query(Artist).filter_by(id=artist_id).one()
  data.genres = data.genres.replace("{","").replace("}","").split(",")
  current_time = datetime.utcnow()
  pastShows = db.session.query(Show.venue_id.label('venue_id'),Venue.image_link.label('venue_image_link'),Show.start_time.label('start_time'),Show.venue_id.label('venue_id'),Venue.name.label('venue_name')).filter_by(artist_id=artist_id).filter(Show.start_time < current_time).outerjoin(Venue).all()
  data.past_shows = pastShows
  upcomingShows = db.session.query(Show.venue_id.label('venue_id'),Venue.image_link.label('venue_image_link'),Show.start_time.label('start_time'),Show.venue_id.label('venue_id'),Venue.name.label('venue_name')).filter_by(artist_id=artist_id).filter(Show.start_time > current_time).outerjoin(Venue).all()
  data.upcoming_shows = upcomingShows
  data.past_shows_count = len(data.past_shows)
  data.upcoming_shows_count = len(data.upcoming_shows)

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm()
  artist = db.session.query(Artist).filter_by(id=artist_id).one()
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm()
  alterArtist = db.session.query(Artist).filter_by(id = artist_id).one()
  alterArtist.name = form.name.data
  alterArtist.genres = form.genres.data
  alterArtist.seeking_venue = form.seeking_venue.data
  if (alterArtist.seeking_venue is True):
        alterArtist.seeking_description = form.seeking_description.data
  alterArtist.website = form.website.data
  alterArtist.image_link = form.image_link.data
  alterArtist.website = form.website.data
  alterArtist.facebook_link = form.facebook_link.data
  alterArtist.phone = form.phone.data
  db.session.commit()
  return redirect(url_for('show_artist', artist_id=artist_id))

#delete artist

@app.route('/artists/<int:artist_id>/delete', methods=['GET'])
def delete_artist(artist_id):
  form = ArtistForm()
  artist = db.session.query(Artist).filter_by(id=artist_id).one()
  return render_template('pages/home.html')

@app.route('/artists/<int:artist_id>/delete', methods=['DELETE'])
def delete_artist_submission(artist_id):
	db.session.query(artist).filter_by(id = artist_id).delete()
	try:
		db.session.commit()
		flash('Artist with id '+artist_id +' was successfully deleted!')
	except Exception as e:
		db.session.rollback()
		db.session.flush()
		flash('Error while deleting the artist '+artist_id)
	return render_template('pages/home.html')

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue = db.session.query(Venue).filter_by(id=venue_id).one()
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    form = VenueForm()
    alterVenue = db.session.query(Venue).filter_by(id = venue_id).one()
    alterVenue.name = form.name.data
    alterVenue.genres = form.genres.data
    alterVenue.seeking_talent = form.seeking_talent.data
    if (alterVenue.seeking_talent is True):
        alterVenue.seeking_description = form.seeking_description.data
    alterVenue.website = form.website.data
    alterVenue.facebook_link = form.facebook_link.data
    alterVenue.phone = form.phone.data
    db.session.commit()
    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
	addArtistForm = ArtistForm()
	addArtist = Artist()
	addArtist.name = addArtistForm.name.data
	addArtist.city = addArtistForm.city.data
	addArtist.state = addArtistForm.state.data
	addArtist.genres = addArtistForm.genres.data
	addArtist.seeking_venue = addArtistForm.seeking_venue.data
	if (addArtist.seeking_venue is True):
		addArtist.seeking_description = addArtistForm.seeking_description.data
	addArtist.website = addArtistForm.website.data
	addArtist.facebook_link = addArtistForm.facebook_link.data
	addArtist.image_link = addArtistForm.image_link.data
	addArtist.phone = addArtistForm.phone.data
	db.session.add(addArtist)
	try:
		db.session.commit()
		flash('Artist ' + addArtistForm.name.data + ' was successfully added!')
	except Exception as e:
		db.session.rollback()
		db.session.flush()
		flash('An error occurred. Artist ' + addArtistFOrm.name.data + ' could not be listed.')
	return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  	data = db.session.query(Venue.id.label('venue_id'),Venue.name.label('venue_name'),Artist.id.label('artist_id'),Artist.name.label('artist_name'),Artist.image_link.label('artist_image_link'),Show.start_time.label('start_time')).outerjoin(Venue).outerjoin(Artist).all()
  	return render_template('pages/shows.html', shows=data)




@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
	addShowForm = ShowForm()
	addShow = Show()
	addShow.artist_id = addShowForm.artist_id.data
	addShow.venue_id = addShowForm.venue_id.data
	addShow.start_time = addShowForm.start_time.data
	db.session.add(addShow)
	try:
		db.session.commit()
		flash('Show was successfully listed!')
	except Exception as e:
		db.session.rollback()
		db.session.flush()
		flash('An error occurred. Show could not be listed.')


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
