from bs4 import BeautifulSoup as bs
from urllib.request import urlopen
from flask_caching import Cache
import time
import yaml
import os
import requests
import re
import pickle
import sys
import html
import subprocess
import tmdbsimple as tmdb
from datetime import datetime
from flask import Flask, render_template, flash, request, redirect, url_for, session, logging
from flask_paginate import Pagination, get_page_parameter
from wtforms import Form, StringField
from flask.ext.babel import Babel, gettext

app = Flask(__name__, static_folder='static', static_url_path='')
app.config['BABEL_DEFAULT_LOCALE'] = 'bg'
cache = Cache(app,config={'CACHE_TYPE': 'simple'})
babel = Babel(app)

LANGUAGES = {
    'en': 'English',
    'bg': 'Bulgarian'
}


@babel.localeselector
def get_locale():
    if request.args.get('lang'):
        session['lang'] = request.args.get('lang')
    return session.get('lang', 'en')

PER_PAGE = 20
MAX_SEARCH_RESULTS = 50

class SearchForm(Form): 
    search = StringField('search')

search_form = SearchForm()

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500

@app.route('/db/')
def db():
	movies = torrents.torrents
	top_movies, movies_count, xserials_count, genres, years, actors = filter_torrents(movies , type = 'movie')
	top_serials, xmovies_count, serials_count, genres, years, actors = filter_torrents(movies, type = 'serial')
	
	updated = arenabg.updated_new

	size = du(arenabg.get_path() + "/data/")
	imdb = du(arenabg.get_path() + "/imdb/")
	trackers = du(arenabg.get_path() + "/trackers/")
	return render_template('db.html', movies_count = movies_count, serials_count = serials_count, updated = updated, size = size, imdb = imdb, trackers = trackers)
	
def du(path):
    """disk usage in human readable format (e.g. '2,1GB')"""
    return subprocess.check_output(['du','-sh', path]).split()[0].decode('utf-8')
	
@app.route('/search', methods=['POST'])
def search():
	search_form = SearchForm(request.form)
	query = search_form.search.data.lower()
	movies = torrents.torrents

	result = [movie for movie in movies if query in movie['Title'].lower()]
	result = result + [movie for movie in movies if query.title() in str(movie['stars'])]
	result = result + [movie for movie in movies if query == movie['Imdb_id'].lower()]
	movies_count = len(result)
	updated = arenabg.updated_new
	
	return render_template('search.html', search_form = search_form,
										query = query, 
										movies = result, 
										movies_count = movies_count,
										title = 'Search for: ' + query,
										updated = updated,
										)
	
@app.route('/update/')
def update():
	alein_org.movies = alein_org.get_cached_list()
	alein_org.new_movies = alein_org.get_new_cached_list()

	arenabg.movies = arenabg.get_cached_list()
	arenabg.new_movies = arenabg.get_new_cached_list()	
	
	zamunda.movies = zamunda.get_cached_list()
	zamunda.new_movies = zamunda.get_new_cached_list()	
	
	zelka.movies = zelka.get_cached_list()
	zelka.new_movies = zelka.get_new_cached_list()
	
	arenabg.updated = arenabg.get_update_date()
	arenabg.updated_new = arenabg.get_update_date()
	
	energy_torrent.movies = energy_torrent.get_cached_list()
	energy_torrent.new_movies = energy_torrent.get_new_cached_list()		

	p2pbg_com.updated = p2pbg_com.get_update_date()
	p2pbg_com.updated_new = p2pbg_com.get_update_date()
	
	torrents.torrents = []
	torrents.add(arenabg.movies + zamunda.movies + zelka.movies + alein_org.movies + energy_torrent.movies + p2pbg_com.movies)
	# torrents.add(arenabg.movies + zamunda.movies + zelka.movies + alein_org.movies + energy_torrent.movies + p2pbg_com.movies)
	return redirect(url_for('index'))

@cache.cached(timeout = 50)	
@app.route('/')
def index():

	movies = torrents.torrents
	top_movies, movies_count, xserials_count, genres, years, actors = filter_torrents(movies, genre = 'All', year = '2018', type = 'movie')
	top_movies = paginate_torrents(top_movies, 5 , 1)
	
	top_serials, xmovies_count, serials_count, genres, years, actors = filter_torrents(movies, type = 'serial')
	
	top_serials = paginate_torrents(top_serials, 5 , 1)

	try:
		new_movies = arenabg.new_movies + zamunda.new_movies + zelka.new_movies + alein_org.new_movies + energy_torrent.new_movies + p2pbg_com.new_movies
		filtered_movies, new_movies_count, xserials_count, genres, years, actors = filter_torrents(new_movies)
	except TypeError:
		new_movies = None
		filtered_movies, new_movies_count = [], 0
	updated = arenabg.updated_new
	try:
		filtered_movies = paginate_torrents(filtered_movies, 5 , 1)
	except IndexError:
		filtered_movies = []
	return render_template('home.html', new_movies = filtered_movies,
										top_movies = top_movies, 
										updated = updated, 
										new_movies_count = new_movies_count,
										top_serials = top_serials,
										movies_count = movies_count,
										serials_count = serials_count,
										search_form = search_form,
										title = 'BG Torrents Mix Home'
										)

	
	
@cache.cached(timeout = 50)
@app.route('/movies/', defaults = {'genre': 'All', 'year': 'All', 'page': 1})
@app.route('/movies/<string:genre>/', defaults = {'page': 1, 'year': 'All'})
@app.route('/movies/<string:genre>/<string:year>/', defaults = {'page': 1})
@app.route('/movies/<string:genre>/<string:year>/<int:page>')
def poster_gallery(genre, year, page):
	movies = torrents.torrents
	filtered_movies, movies_count, serials_count, genres, years, actors = filter_torrents(movies, genre, year, 'movie')
	filtered_movies = paginate_torrents(filtered_movies, PER_PAGE, page)
	pagination = Pagination(page = page,
							total = movies_count,
							css_framework = 'bootstrap',
							per_page = PER_PAGE, 
							record_name = 'movies',
							bs_version = 3,
							outer_window = 1,
							inner_window = 4,
							
							)
	
	updated = arenabg.updated
	
	title = genre + ' Movies sorted by IMDB - page: ' + str(page)
	
	return render_template('poster_gallery.html',
							movies = filtered_movies, 
							movies_count = movies_count,
							genres = genres,
							years = years,
							genre = genre,
							year = year,
							updated = updated,
							pagination = pagination,
							search_form = search_form,
							title = title,
							actors = actors,
							)

@cache.cached(timeout = 50)
@app.route('/new_movies/', defaults = {'genre': 'All', 'year': 'All'})
@app.route('/new_movies/<string:genre>/<string:year>')
def new_movies(genre, year):
	try:
		new_movies = arenabg.new_movies + zelka.new_movies + zamunda.new_movies + alein_org.new_movies + energy_torrent.new_movies + p2pbg_com.new_movies
	except TypeError:
		new_movies = []
	filtered_movies, movies_count, serials_count, genres, years, actors = filter_torrents(new_movies, genre, year)
	updated = arenabg.updated_new
	
	title = genre + gettext(' New torrents sorted by IMDB')
	
	return render_template('new_movies.html',
							movies = filtered_movies, 
							movies_count = movies_count,
							genres = genres,
							years = years,
							genre = genre,
							year = year,
							updated = updated,
							search_form = search_form,
							title = title,
							actors = actors,
							)

							
@cache.cached(timeout = 50)
@app.route('/tv_series/', defaults={'genre': 'All', 'year': 'All', 'page': 1})		
@app.route('/tv_series/<string:genre>/', defaults = {'page': 1, 'year': 'All'})	
@app.route('/tv_series/<string:genre>/<string:year>/', defaults = {'page': 1})				
@app.route('/tv_series/<string:genre>/<string:year>/<int:page>')
def tv_series(genre, year, page):
	serials = torrents.torrents
	filtered_serials, movies_count, serials_count, genres, years, actors = filter_torrents(serials, genre, year, 'serial')
	filtered_serials = paginate_torrents(filtered_serials, PER_PAGE, page)
	pagination = Pagination(page = page,
							total = serials_count,
							css_framework = 'bootstrap',
							per_page = PER_PAGE, 
							record_name = 'tv series',
							bs_version = 3,
							outer_window = 1,
							inner_window = 4,
							
							)	
	updated = arenabg.updated
	
	title = genre + ' New tv series sorted by IMDB - page: ' + str(page)
	
	return render_template('tv_serials.html',
							movies = filtered_serials, 
							serials_count = serials_count,
							genres = genres,
							years = years,
							genre = genre,
							year = year,
							updated = updated,
							pagination = pagination,
							search_form = search_form,
							title = title,
							actors = actors,
							)

# filters the movies based on user reqest							
def filter_torrents(movies, genre = 'All', year = 'All', type = 'movie'):
	movies = separate(movies, type)
	movies = remove_dupl(movies)
	movies = sorted(movies, key = getKey, reverse = True)
	genres = get_genres(movies)	
	actors = get_actors(movies)	
	filtered_movies = []
	if genre == 'All':
		filtered_movies = movies
	else:
		filtered_movies = [movie for movie in movies if genre in movie['Genre_str']]
				
	movies = filtered_movies
	
	filtered_movies = []
	if year == 'All':
		filtered_movies = movies
	else:
		filtered_movies = [movie for movie in movies if year in movie['Year']]
	
	years = get_years(movies)
	movies_count, serials_count = count_torrents(filtered_movies)	
	return filtered_movies, movies_count, serials_count, genres, years, actors

def count_torrents(filtered_movies):
	movies_count = 0
	serials_count = 0
	for movie in filtered_movies:
		if movie['Type'] == 'movie':
			movies_count += 1
		else:
			serials_count += 1	
	return movies_count, serials_count
	
# returns movies or serials only
def separate(movies, type):
	separated = [movie for movie in movies if type == movie['Type']]
		
	separated = [movie for movie in separated if not movie['Year'] == None]
	return separated

# used for soring list of dics							
def getKey(item):
	return str(item['imdbRating'])
		
# Removes torrents with duplicate IMDB ID
def remove_dupl(movies):
	imdb_ids = []
	unique_movies = []
	for movie in movies:
		if movie['Imdb_id'] not in imdb_ids:
			imdb_ids.append(movie['Imdb_id'])
			unique_movies.append(movie)
	return unique_movies
	
# build genres list
def get_genres(movies):
	geners = set()
	for movie in movies:
		for genre in movie['Genre']:
			if len(genre) > 0:
				geners.add(genre.strip())
	geners = list(geners)
	geners.sort()
	
	return geners

# build genres list
def get_actors(movies):
	actors = set()
	for movie in movies:
		for actor in movie['stars']:
			actors.add(actor)
	actors = list(actors)
	actors.sort()
	
	return actors	
	
# build years list
def get_years(movies):
	years = set()
	for movie in movies:
		if '–' in str(movie['Year']):
			years.add(str(movie['Year']).split('–')[0])
		else:			
			if not movie['Year'] == None:
				years.add(movie['Year'])
	years = list(years)
	try:
		years.sort(reverse=True)
	except TypeError:
		years = []
	return years	

def paginate_torrents(torrents, per_page, page):
	paginated = [torrents[i:i + per_page] for i in range(0, len(torrents), per_page)]
	return paginated[page - 1]
	
# load configuratin variables for trackers
CONFIG = open(os.path.dirname(os.path.realpath(sys.argv[0])) + '/config.yaml')
CONFIG_DATA = yaml.safe_load(CONFIG)

THEMOVIEDB_API_KEY = CONFIG_DATA['themoviedb_api_key']

FETCH_DELAY = CONFIG_DATA['fetch_delay']
TRACKER_CACHE_FOLDER = CONFIG_DATA['tracker_cache_folder']
IMDB_CACHE_FOLDER = CONFIG_DATA['imdb_cache_folder']
DEBUG = CONFIG_DATA['debug']
PAGES_TO_SCAN = CONFIG_DATA['pages_to_scan']
MISSING_IMDB_POSTER = "/images/poster.jpg"

# arenabg.com
ARENABG_FORM_DATA = CONFIG_DATA['arenabg_form_data']
ARENABG_LOGIN_URL = CONFIG_DATA['arenabg_login_url']
ARENABG_INTERNAL_URL = CONFIG_DATA['arenabg_internal_url']

# zamunda.net
ZAMUNDA_INTERNAL_URL = CONFIG_DATA['zamunda_internal_url']
ZAMUNDA_LOGIN_URL = CONFIG_DATA['zamunda_login_url']
ZAMUNDA_FORM_DATA = CONFIG_DATA['zamunda_form_data']

# zelka.org
ZELKA_INTERNAL_URL = CONFIG_DATA['zelka_internal_url']
ZELKA_LOGIN_URL = CONFIG_DATA['zelka_login_url']
ZELKA_FORM_DATA = CONFIG_DATA['zelka_form_data']

# alien_org
ALIEN_ORG_INTERNAL_URL = CONFIG_DATA['alien_org_internal_url']
ALIEN_ORG_LOGIN_URL = CONFIG_DATA['alien_org_login_url']
ALIEN_ORG_FORM_DATA = CONFIG_DATA['alien_org_form_data']

# energy_torrent
ENERGY_TORRENT_INTERNAL_URL = CONFIG_DATA['energy_torrent_internal_url']
ENERGY_TORRENT_LOGIN_URL = CONFIG_DATA['energy_torrent_login_url']
ENERGY_TORRENT_FORM_DATA = CONFIG_DATA['energy_torrent_form_data']

# p2pbg_com
P2PBG_COM_INTERNAL_URL = CONFIG_DATA['p2pbg_com_internal_url']
P2PBG_COM_LOGIN_URL = CONFIG_DATA['p2pbg_com_login_url']
P2PBG_COM_FORM_DATA = CONFIG_DATA['p2pbg_com_form_data']

class Torrents():
	def __init__(self, torrents):
		self.torrents = []
		self.new_torrents = []
		self.movies = []
		self.tv_series = []
		
	def add(self, torrents):
		self.torrents = self.torrents + torrents
		self.movies = [movie for movie in self.torrents if movie['Type'] == 'movie']
		self.tv_series = [movie for movie in self.torrents if movie['Type'] == 'serial']
		
		# self.new_torrents = [movie for movie in self.torrents if movie['New']]
		
		
class Arenabg():
	tracker_urls_served = 0
	imdb_urls_served = 0
	total_movies = 0
	
	def __init__(self, login_url, user_data):		
		self.user_data = user_data
		self.login_url = login_url
		self.tracker_login_session = self.tracker_login()
		self.tracker_name = self.login_url.split('/')[2]
		self.movies = self.get_cached_list()
		self.new_movies = self.get_new_cached_list()
		self.updated = self.get_update_date()
		self.updated_new = self.get_update_date()
		
	# get data generation timestamp
	@staticmethod
	def get_update_date():
		try:
			updated = time.strftime("%m/%d/%Y %I:%M:%S %p",
						time.localtime(os.path.getmtime(Arenabg.get_path() + '/data/zelka.org'))
									)
		except FileNotFoundError:
			print('File not found')
			return None
		return updated
		
	# create and return the torrent site login session	
	def tracker_login(self):
		tracker_login_session = requests.Session()
		tracker_login_session.post(self.login_url, data = self.user_data , verify=False)
		return tracker_login_session
		
	#returns all torrent details urls
	def get_movies(self):
		subs_url = ARENABG_INTERNAL_URL + 'subtitles:1/page:'
		bg_audio_url = ARENABG_INTERNAL_URL + 'audio:1/page:'
		pageurls = []
		
		for i in range(1, PAGES_TO_SCAN + 1 , 1):
			pageurls.append(subs_url + str(i))
		for i in range(1, PAGES_TO_SCAN + 1 , 1):
			pageurls.append(bg_audio_url + str(i))	
			
		urls = set()
		for url in pageurls:
			if DEBUG:
				print('Processing {} urls - current {}'.format(len(pageurls), url))
				
			self.tracker_urls_served += 1
			response = self.tracker_login_session.get(url)
			html = response.text
			soup = bs(html, 'html.parser')
			for link in soup.findAll('a', attrs = {'class': 'torrent-link'}):
				urls.add('http://arenabg.com' + link['href'])	
			time.sleep(FETCH_DELAY)
			
		self.total_movies = len(urls)
		return urls
		
	#return the imdb-id of tracker url
	def get_movie_imdb_id(self, url):
		self.tracker_urls_served += 1
		file_name = re.sub('[^A-Za-z0-9]+', '', url)
		
		try:			
			imdb_id = pickle.load(open(os.path.join(self.get_path(),
													TRACKER_CACHE_FOLDER, 
													file_name), 'rb')
													)
			try:
				imdb_id = imdb_id.replace(' ', '')
			except:
				pass
			return imdb_id
		except:
			if DEBUG:
				print('------ get imdb id ------- sleep {} s'.format(FETCH_DELAY))
			time.sleep(FETCH_DELAY)
			response = self.tracker_login_session.get(url)
			html = response.text		
			link = []
			soup = bs(html) 
			# print(url)
			for link in soup.findAll('a'):
				if 'www.imdb.com' in str(link):
					imdb_id = link['href'].split('/')
					# print(imdb_id)
					for id in imdb_id:
						if id[:2] == 'tt':
							imdb_id = id

					if imdb_id[:2] == 'tt':
						if DEBUG:
							print(imdb_id + ' New movie imdbid')
						pickle.dump(imdb_id,
									open(self.get_path() 
									+ '/{}/{}'.format(TRACKER_CACHE_FOLDER, file_name), "wb"))
						return imdb_id.replace(' ', '')
					else:
						print("invalid imdbid", imdb_id)
						
						return False
		
			pickle.dump( False, open('{}/{}/{}'.format(self.get_path(),
												TRACKER_CACHE_FOLDER, file_name), 'wb'))
			
		return False
	
	@staticmethod
	#returns script location path
	def get_path():
		return os.path.dirname(os.path.realpath(sys.argv[0]))

	#extract movie data from IMDB site
	@staticmethod
	def get_media_imdb(imdbid):
		Arenabg.imdb_urls_served += 1		
		try:			
			result = pickle.load(open(Arenabg.get_path()+ '/imdb/'+ imdbid, 'rb'))
			new = False
			
			return result, new			
		except:
			if DEBUG:
				print('------ get imdb data ------- sleep {} s'.format(FETCH_DELAY))
			
			new = True
			url = 'http://www.imdb.com/title/{}/'.format(imdbid)
			try:
				soup = bs(urlopen(url), 'html.parser')
				time.sleep(FETCH_DELAY)
			except:
				return None, False
			# parse rating
			ss = soup.findAll('span',attrs={'itemprop':'ratingValue'})
			try:
				rating = str(ss).split(">")[1].split("<")[0]	
			except:
				rating = '0'
			# parse poster
			try:
				poster = soup.findAll('div',attrs={'class':'poster'})
				poster = str(poster).split('"')[9]
			except:
				poster = MISSING_IMDB_POSTER		
			# parse genre
			gen = soup.findAll('div',attrs={'class':'subtext'})
			x = bs(str(gen), "html.parser")
			gen = x.findAll('span',attrs={'class':'itemprop'})
			genre = re.sub('<[^<]+?>', '', str(gen))
			genre = genre.strip('[').strip(']').strip(' ').split(",")
			
			# parse stars
			stars = soup.findAll('span',attrs={'itemprop':'actors'})
			stars = (re.sub('<[^<]+?>', '', str(stars)).replace('\n', '')
														.replace('[', '')
														.replace(']', '')
														.replace('             ', '')
														.replace(',, ',',')
														.rstrip()
														.split(',')
														)
			stars = list(filter(None, stars))
			genre_str = ', '.join(genre)
			
			# parse title
			t = soup.findAll('meta', attrs = {'property': 'og:title'})
			title = html.unescape(str(t).split('"')[1])
			if '(' in title:
				title = title.split('(')[0]
			if len(title) < 1:
				return None, False
			# parse year	
			try:
				type = 'movie'
				title_year = soup.find('span', {'id': 'titleYear'}).find('a').get_text()				
			except:
				type = 'serial'
				try:
					title_year = soup.find('a', {'title': 'See more release dates'})
					title_year = title_year.get_text().strip().split('(')[1].split(')')[0]
				except:
					try:
						title_year = str(soup.find('span', {'class': 'parentDate'})
													.get_text()
													.strip()
													)
						title_year = title_year.replace('(', '').replace(')', '')
					except:
						title_year = None
						
				

			result = {'Imdb_id': imdbid, 'Type': type,
						'Year': title_year, 'Title': title,
						'imdbRating': rating, 'Poster': poster,
						'Genre': genre, 'Genre_str': genre_str,
						'stars': stars
						}
			pickle.dump(result, 
						open('{}/imdb/{}'.format(Arenabg.get_path(), imdbid),
						'wb' ))			
		return result, new
		
	def get_trailer(self, title):
		tmdb.API_KEY = THEMOVIEDB_API_KEY
		search = tmdb.Search()
		response = search.movie(query=title)
		return search.results
	
	#returns a lists of movies with their imdb data
	def get_list(self):
		list = []
		imdb_ids_list = []
		for movie in self.get_movies():
				try:
					if DEBUG:
						print('total urls: {} - procesed urls: {} - imdb urls: {}'
							.format(self.total_movies, 
									self.tracker_urls_served, 
									self.imdb_urls_served))
				
					imdb_id = self.get_movie_imdb_id(movie)
					if imdb_id :
						if imdb_id not in imdb_ids_list:
							movie_data, is_movie_new = self.get_media_imdb(imdb_id)
							if DEBUG:
								print(movie)
							if movie_data and imdb_id:
								movie_data['url'] = movie
								movie_data['New'] = is_movie_new
								list.append(movie_data)
								imdb_ids_list.append(imdb_id)
				except ConnectionError:
					print('connection error ----------------------------------------------')
					
		return list
		
	def save_list(self):
		def getKey(item):
			return str(item['imdbRating'])
		movies = sorted(self.get_list(), key = getKey, reverse = True)
		pickle.dump(movies, open(self.get_path() 
									+ '/data/' + self.tracker_name, 'wb'))
		self.save_new(movies)
		
	# Saves newly discovered torrents
	def save_new(self, movies):
		new_torrents = []
		try:
			old_torrents = pickle.load(open(self.get_path() 
									+ '/data/' + self.tracker_name + '_new', 'rb'))
		except:
			old_torrents = []
			
		for movie in movies:
			if movie['New']:
				new_torrents.append(movie)
		new_torrents = new_torrents + old_torrents
		pickle.dump(new_torrents, open(self.get_path() 
									+ '/data/' + self.tracker_name + '_new', 'wb'))
	
	def get_cached_list(self):
		try:			
			result = pickle.load(open(Arenabg.get_path() 
									+ '/data/' + self.tracker_name, 'rb'))
			return result
		except:
			return False

	def get_new_cached_list(self):
		try:			
			result = pickle.load(open(Arenabg.get_path() 
									+ '/data/' + self.tracker_name + '_new', 'rb'))
			return result
		except:
			return False
			
class Zamunda(Arenabg):
	#get tracker movies urls
	def get_movies(self):
		pageurls = []
		#Builds a list of urls to be scanned - bg subs
		for i in range(0, PAGES_TO_SCAN , 1): 
			pageurls.append(ZAMUNDA_INTERNAL_URL + '?field=name&bgsubs=1&page=' + str(i))
		#Builds a list of urls to be scanned -  bg audio
		for i in range(0, PAGES_TO_SCAN , 1): 
			pageurls.append(ZAMUNDA_INTERNAL_URL + '?field=name&bgaudio=1&page=' + str(i))
		urls = set()
		for url in pageurls: #gets the links from each url	
			if DEBUG:
				print('Processing {} urls - current {}'.format(len(pageurls),url))
				
			response = self.tracker_login_session.get(url)
			html = response.text
			soup = bs(html, 'html5lib') 
			for link in soup.findAll('a',href=True):

				if 'banan?id=' in link['href'] and 'javascript' not in link['href']:
					if not link['href'].startswith('/'):
						try:
							urls.add('http://zamunda.net/' + link['href'].split('&')[0])
						except:
							urls.add('http://zamunda.net/' + link['href'])
			time.sleep(FETCH_DELAY)
		self.total_movies = len(urls)	
		return urls


class Zelka(Arenabg):
	#get tracker movies urls
	def get_movies(self):
		pageurls = []
		for i in range(1, PAGES_TO_SCAN + 1, 1):
			pageurls.append(ZELKA_INTERNAL_URL 
							+ '?page=' 
							+ str(i) 
							+ '&sort=12&type=desc'
							)
			
		urls = set()
		for url in pageurls: 
			if DEBUG:
				print('Processing {} urls - current {}'.format(len(pageurls),url))
				
			response = self.tracker_login_session.get(url)
			html = response.text
			soup = bs(html, 'html5lib') 
			# get all torrent details urls on the current page
			for link in soup.findAll('a', href = True): 
				if 'details.php?id=' in link['href'] and 'hit' not in link['href']:
					if 'userdetails' not in link['href']:
						urls.add('http://zelka.org/' + link['href'])	
						
			time.sleep(FETCH_DELAY)
		self.total_movies = len(urls)
		return urls
	
	
class Alein_org(Arenabg):
	#get tracker movies urls
	def get_movies(self):
		pageurls = []
		for i in range(1, PAGES_TO_SCAN + 1, 1):
			pageurls.append(ALIEN_ORG_INTERNAL_URL 
							+ '&ssubs=1&active=1&order=3&by=2&pages=' 
							+ str(i) 
							)
			
		urls = set()
		for url in pageurls: 
			if DEBUG:
				print('Processing {} urls - current {}'.format(len(pageurls),url))
				
			response = self.tracker_login_session.get(url)
			html = response.text
			soup = bs(html) 
			# get all torrent details urls on the current page
			for link in soup.findAll('a'): 
				#print(link)
				if 'page=torrent-details' in link['href']:
					urls.add('http://alein.org/' + link['href'])	
						
			time.sleep(FETCH_DELAY)
		self.total_movies = len(urls)
		return urls

		
class Energy_torrent(Arenabg):
	#get tracker movies urls
	def get_movies(self):
		pageurls = []
		#Builds a list of urls to be scanned
		for i in range(0, PAGES_TO_SCAN , 1): 
			pageurls.append(ENERGY_TORRENT_INTERNAL_URL + '?page=' + str(i))
		urls = set()
		for url in pageurls: #gets the links from each url	
			if DEBUG:
				print('Processing {} urls - current {}'.format(len(pageurls),url))
				
			response = self.tracker_login_session.get(url)
			html = response.text
			soup = bs(html, 'html5lib') 
			for link in soup.findAll('a',href=True):

				if ('details.php' in link['href'] and 'bookmark.php' not in link['href'] 
				and 'list' not in link['href'] and 'toseeders' not in link['href'] 
				and 'tocomm' not in link['href'] and 'todlers' not in link['href']):
					urls.add('http://energy-torrent.com/' + link['href'])
			time.sleep(FETCH_DELAY)
		self.total_movies = len(urls)
		return urls

		
class P2pbg_com(Arenabg):
	#get tracker movies urls
	def get_movies(self):
		pageurls = []
		#Builds a list of urls to be scanned
		for i in range(0, PAGES_TO_SCAN , 1): 
			pageurls.append(P2PBG_COM_INTERNAL_URL + '&pages=' + str(i + 1))
		urls = set()
		for url in pageurls: #gets the links from each url	
			if DEBUG:
				print('Processing {} urls - current {}'.format(len(pageurls),url))
				
			response = self.tracker_login_session.get(url)
			html = response.text
			soup = bs(html, 'html5lib') 
			for link in soup.findAll('a',href=True):

				if ('page=torrent-details' in link['href'] and '#comments' not in link['href']):
					urls.add('http://p2pbg.com/' + link['href'])
			time.sleep(FETCH_DELAY)
		self.total_movies = len(urls)

		return urls		
		
if __name__ == '__main__':	
	arenabg = Arenabg(ARENABG_LOGIN_URL, ARENABG_FORM_DATA)
	zamunda = Zamunda(ZAMUNDA_LOGIN_URL, ZAMUNDA_FORM_DATA)
	zelka = Zelka(ZELKA_LOGIN_URL, ZELKA_FORM_DATA)
	alein_org = Alein_org(ALIEN_ORG_LOGIN_URL, ALIEN_ORG_FORM_DATA)
	energy_torrent = Energy_torrent(ENERGY_TORRENT_LOGIN_URL, ENERGY_TORRENT_FORM_DATA)
	p2pbg_com = P2pbg_com(P2PBG_COM_LOGIN_URL, P2PBG_COM_FORM_DATA)

	torrents = Torrents(arenabg)
	torrents.add(arenabg.movies + zamunda.movies + zelka.movies + alein_org.movies + energy_torrent.movies + p2pbg_com.movies)
#	print(torrents.torrents)
	# for t in arenabg.movies:
		# time.sleep(FETCH_DELAY)
		# print(arenabg.get_trailer(t['Title']))
	app.secret_key='bgtorrentskey123'
	app.run(debug=False, 
		host='0.0.0.0', 
		port=5000, 
		threaded=True)