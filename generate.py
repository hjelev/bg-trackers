from datetime import datetime
from index import *
from urllib.request import urlopen


if __name__ == '__main__':	
	start_time = datetime.now()
	
	alein_org = Alein_org(ALIEN_ORG_LOGIN_URL, ALIEN_ORG_FORM_DATA)
	arenabg = Arenabg(ARENABG_LOGIN_URL, ARENABG_FORM_DATA)
	zamunda = Zamunda(ZAMUNDA_LOGIN_URL, ZAMUNDA_FORM_DATA)
	zelka = Zelka(ZELKA_LOGIN_URL, ZELKA_FORM_DATA)
	energy_torrent = Energy_torrent(ENERGY_TORRENT_LOGIN_URL, ENERGY_TORRENT_FORM_DATA)
	p2pbg_com = P2pbg_com(P2PBG_COM_LOGIN_URL, P2PBG_COM_FORM_DATA)
	
	p2pbg_com.save_list()
	energy_torrent.save_list()
	alein_org.save_list()
	arenabg.save_list()
	zamunda.save_list()
	zelka.save_list()	

	alein_org.movies = zelka.get_cached_list()
	alein_org.new_movies = zelka.get_new_cached_list()	
	
	arenabg.movies = arenabg.get_cached_list()
	arenabg.new_movies = arenabg.get_new_cached_list()
	
	zamunda.movies = zamunda.get_cached_list()
	zamunda.new_movies = zamunda.get_new_cached_list()
	
	zelka.movies = zelka.get_cached_list()
	zelka.new_movies = zelka.get_new_cached_list()	

	energy_torrent.movies = energy_torrent.get_cached_list()
	energy_torrent.new_movies = energy_torrent.get_new_cached_list()	

	p2pbg_com.movies = p2pbg_com.get_cached_list()
	p2pbg_com.new_movies = p2pbg_com.get_new_cached_list()
	
	arenabg.updated = arenabg.get_update_date()
	arenabg.updated_new = arenabg.get_update_date()
	
	end_time = datetime.now()
	print('Duration: {}'.format(end_time - start_time))
	urlopen('http://192.168.0.102:5000/update/')