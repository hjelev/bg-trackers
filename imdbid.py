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

DEBUG = True
FETCH_DELAY = 0
		
def get_media_imdb(imdbid):
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
				'stars': stars,
				}
			
	return result, new

if __name__ == '__main__':	
	print(get_media_imdb('tt1856101'))