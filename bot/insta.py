from instaloader import Instaloader, Post
from config import INSTA_USER, INSTA_PASSWORD, PATH_DOWNLOADS, INSTA_SESSION
import logging
import datetime as dt
import re
import os
from pathlib import Path
from sqlalchemy.orm import scoped_session, sessionmaker
from dbmap import write_media_to_db, TgUser, self_user
from config import logger

insta = Instaloader()

logger.info('Логинимся в Instagram...')
insta.login(INSTA_USER, INSTA_PASSWORD)
# insta.save_session_to_file(filename=INSTA_SESSION)
insta.load_session_from_file(INSTA_USER, INSTA_SESSION)
logger.info('Залогинились успешно!')

PATH = Path(PATH_DOWNLOADS, dt.datetime.now().strftime('%d-%m-%Y'))
regex_filter_url = '(?:https?:\/\/)?(?:www.)?instagram.com\/?([a-zA-Z0-9\.\_\-]+)?\/([p]+)?([reel]+)?([tv]+)?([stories]+)?\/([a-zA-Z0-9\-\_\.]+)\/?([0-9]+)?'

def insta_download_post(message:str,path:str=PATH,user:TgUser=self_user):
	try:
		text =''
		shortcode = re.split(regex_filter_url, message)[6]
		path = Path(path, shortcode)
		post = Post.from_shortcode(insta.context, shortcode)
		insta.download_post(post, path)
		files = absoluteFilePaths(path)
		for file in files:
			if 'txt' in file:
				with open(file, "r", encoding="utf-8") as f:
					text = ''.join(f.readlines())
		files = [file for file in files if 'jpg' in file or 'mp4' in file]
		for file in files:
			if 'mp4' in file:
				files.remove(file[:-4] + '.jpg')
		logger.info(f'Успешное скачивание: {shortcode}')
		write_media_to_db(files, shortcode, text, user)
		return True, files, text
	except Exception as error:
		logger.info(f'Не удалось скачать {shortcode}, ошибка: {error}')
		return False, [], 'Ошибка: ' + str(error)

def absoluteFilePaths(directory):
		files = []
		for dirpath,_,filenames in os.walk(directory):
			for f in filenames:
				files.append(os.path.abspath(os.path.join(dirpath, f)))
		return files
	

