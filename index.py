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
from datetime import datetime
from flask import Flask, render_template, flash, request, redirect, url_for, session, logging
from flask_paginate import Pagination, get_page_parameter
from wtforms import Form, StringField

app = Flask(__name__)
cache = Cache(app,config={'CACHE_TYPE': 'simple'})

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
	
@app.route('/search', methods=['POST'])
def search():
	search_form = SearchForm(request.form)
	query = search_form.search.data.lower()
	movies = arenabg.movies + zamunda.movies + zelka.movies + alein_org.movies

	result = [movie for movie in movies if query in movie['Title'].lower()]
	result = result + [movie for movie in movies if query == movie['Imdb_id'].lower()]
	movies_count = len(result)
	return render_template('search.html', search_form = search_form,
										query = query, 
										movies = result, 
										movies_count = movies_count,
										title = 'Search for: ' + query
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
	return redirect(url_for('index'))
	
@app.route('/')
def index():

	movies = arenabg.movies + zamunda.movies + zelka.movies + alein_org.movies
	top_movies, movies_count, xserials_count, genres, years = filter_torrents(movies, genre = 'All', year = '2017', type = 'movie')
	top_movies = paginate_torrents(top_movies, 5 , 1)
	
	top_serials, xmovies_count, serials_count, genres, years = filter_torrents(movies, type = 'serial')
	
	top_serials = paginate_torrents(top_serials, 5 , 1)

	try:
		new_movies = arenabg.new_movies + zamunda.new_movies + zelka.new_movies + alein_org.new_movies
		filtered_movies, new_movies_count, xserials_count, genres, years = filter_torrents(new_movies)
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

	
	
@cache.cached(timeout=50)
@app.route('/poster_gallery/', defaults = {'genre': 'All', 'year': 'All', 'page': 1})
@app.route('/poster_gallery/<string:genre>/', defaults = {'page': 1, 'year': 'All'})
@app.route('/poster_gallery/<string:genre>/<string:year>/', defaults = {'page': 1})
@app.route('/poster_gallery/<string:genre>/<string:year>/<int:page>')
def poster_gallery(genre, year, page):
	movies = arenabg.movies + zamunda.movies + zelka.movies + alein_org.movies
	filtered_movies, movies_count, serials_count, genres, years = filter_torrents(movies, genre, year, 'movie')
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
							title = title
							)

@cache.cached(timeout=50)
@app.route('/new_movies/', defaults = {'genre': 'All', 'year': 'All'})
@app.route('/new_movies/<string:genre>/<string:year>')
def new_movies(genre, year):
	# print(genre, year)
	try:
		new_movies = arenabg.new_movies + zelka.new_movies + zamunda.new_movies + alein_org.new_movies
	except TypeError:
		new_movies = []
	filtered_movies, movies_count, serials_count, genres, years = filter_torrents(new_movies, genre, year)
	updated = arenabg.updated_new
	
	title = genre + ' New torrents sorted by IMDB'
	
	return render_template('new_movies.html',
							movies = filtered_movies, 
							movies_count = movies_count,
							genres = genres,
							years = years,
							genre = genre,
							year = year,
							updated = updated,
							search_form = search_form,
							title = title
							)

							
@cache.cached(timeout=50)
@app.route('/tv_serials/', defaults={'genre': 'All', 'year': 'All', 'page': 1})		
@app.route('/tv_serials/<string:genre>/', defaults = {'page': 1, 'year': 'All'})	
@app.route('/tv_serials/<string:genre>/<string:year>/', defaults = {'page': 1})				
@app.route('/tv_serials/<string:genre>/<string:year>/<int:page>')
def tv_serials(genre, year, page):
	serials = arenabg.movies + zelka.movies + zamunda.movies + alein_org.movies
	filtered_serials, movies_count, serials_count, genres, years = filter_torrents(serials, genre, year, 'serial')
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
							)

# filters the movies based on user reqest							
def filter_torrents(movies, genre = 'All', year = 'All', type = 'movie'):
	movies = separate(movies, type)
	movies = remove_dupl(movies)
	movies = sorted(movies, key = getKey, reverse = True)
	genres = get_genres(movies)	
	
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
		for movie in movies:
			if year in str(movie['Year']):
				filtered_movies.append(movie)
	
	years = get_years(movies)
	
	movies_count = 0
	serials_count = 0

	for movie in filtered_movies:
		if movie['Type'] == 'movie':
			movies_count += 1
		else:
			serials_count += 1
	
	return filtered_movies, movies_count, serials_count, genres, years

# returns movies or serials only
def separate(movies, type):
	separated = []
	for movie in movies:
		if movie['Type'] == type:
			separated.append(movie)
	return separated

# used for soring list of dics							
def getKey(item):
	return str(item['imdbRating'])
		
# Removes torrents with duplicate IMDB ID
def remove_dupl(movies):
	imdb_ids = []
	unique_movies = []
	for movie in movies:
		if movie['Imdb_id'] in imdb_ids:
			pass
		else:
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

# build years list
def get_years(movies):
	years = set()
	for movie in movies:
		if '–' in str(movie['Year']):
			years.add(str(movie['Year']).split('–')[0])
		else:
			years.add(movie['Year'])
	years = list(years)
	years.sort(reverse=True)
	return years	

def paginate_torrents(torrents, per_page, page):
	paginated = [torrents[i:i + per_page] for i in range(0, len(torrents), per_page)]
	return paginated[page - 1]
	
#load configuratin variables for trackers
CONFIG = open(os.path.dirname(os.path.realpath(sys.argv[0])) + '/config.yaml')
CONFIG_DATA = yaml.safe_load(CONFIG)

FETCH_DELAY = CONFIG_DATA['fetch_delay']
TRACKER_CACHE_FOLDER = CONFIG_DATA['tracker_cache_folder']
IMDB_CACHE_FOLDER = CONFIG_DATA['imdb_cache_folder']
DEBUG = CONFIG_DATA['debug']
PAGES_TO_SCAN = CONFIG_DATA['pages_to_scan']
MISSING_IMDB_POSTER = "/static/images/poster.jpg"

#arenabg.com
ARENABG_FORM_DATA = CONFIG_DATA['arenabg_form_data']
ARENABG_LOGIN_URL = CONFIG_DATA['arenabg_login_url']
ARENABG_INTERNAL_URL = CONFIG_DATA['arenabg_internal_url']

#zamunda.net
ZAMUNDA_INTERNAL_URL = CONFIG_DATA['zamunda_internal_url']
ZAMUNDA_LOGIN_URL = CONFIG_DATA['zamunda_login_url']
ZAMUNDA_FORM_DATA = CONFIG_DATA['zamunda_form_data']

#zelka.org
ZELKA_INTERNAL_URL = CONFIG_DATA['zelka_internal_url']
ZELKA_LOGIN_URL = CONFIG_DATA['zelka_login_url']
ZELKA_FORM_DATA = CONFIG_DATA['zelka_form_data']

#alien_org
ALIEN_ORG_INTERNAL_URL = CONFIG_DATA['alien_org_internal_url']
ALIEN_ORG_LOGIN_URL = CONFIG_DATA['alien_org_login_url']
ALIEN_ORG_FORM_DATA = CONFIG_DATA['alien_org_form_data']

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
			updated = time.strftime("%m/%d/%Y %I:%M:%S %p",time.localtime(os.path.getmtime(Arenabg.get_path() + '/data/arenabg.com')))
		except FileNotFoundError:
			print('File not found')
			return None
		return updated
		
	# create and return the torrent site login session	
	def tracker_login(self):
		tracker_login_session = requests.Session()
		tracker_login_session.post(self.login_url, data = self.user_data)
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
			imdb_id = pickle.load(open(os.path.join(self.get_path(), TRACKER_CACHE_FOLDER, file_name), 'rb'))
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
			soup = bs(html, 'html.parser') 
			for link in soup.findAll('a'):
				if 'www.imdb.com' in str(link):
					imdb_id = link['href'].split('/')
					
					for id in imdb_id:
						if 'tt' in id:
							imdb_id = id
							
					# imdb_id = link['href'].split('/')[4].strip().replace(' ', '')
					
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
						
			genre_str = ', '.join(genre)		
			# print(genre_str)	
			result = {'Imdb_id': imdbid, 'Type': type,
						'Year': title_year, 'Title': title,
						'imdbRating': rating, 'Poster': poster,
						'Genre': genre, 'Genre_str': genre_str,
						}
			pickle.dump(result, 
						open('{}/imdb/{}'.format(Arenabg.get_path(), imdbid),
						'wb' ))			
		return result, new
		
	#returns a lists of movies with their imdb data
	def get_list(self):
		list = []
		imdb_ids_list = []
		for movie in self.get_movies():
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
			old_torrents = pickle.load(open(self.get_path() + '/data/' + self.tracker_name + '_new', 'rb'))
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
		#http://alein.org/index.php?page=torrents&ssubs=1&active=1&order=3&by=2&pages=2
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
			#print(soup.findAll('a'))
			for link in soup.findAll('a'): 
				#print(link)
				if 'page=torrent-details' in link['href']:
					urls.add('http://alein.org/' + link['href'])	
						
			time.sleep(FETCH_DELAY)
		self.total_movies = len(urls)
		#print(urls)
		return urls


if __name__ == '__main__':	
	arenabg = Arenabg(ARENABG_LOGIN_URL, ARENABG_FORM_DATA)
	zamunda = Zamunda(ZAMUNDA_LOGIN_URL, ZAMUNDA_FORM_DATA)
	zelka = Zelka(ZELKA_LOGIN_URL, ZELKA_FORM_DATA)
	alein_org = Alein_org(ALIEN_ORG_LOGIN_URL, ALIEN_ORG_FORM_DATA)
	app.secret_key='bgtorrentskey123'
	app.run(debug=False, 
		host='0.0.0.0', 
		port=5000, 
		threaded=True)