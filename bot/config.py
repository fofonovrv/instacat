import os
from logging.config import dictConfig
from logging import getLogger, StreamHandler

# BASE_DIR = Path(__file__).resolve().parent.parent
INSTA_USER = 'catinstabot'
INSTA_PASSWORD = 'papasong3'
INSTA_SESSION = 'insta_settings.json'
INSTA_LOCATE = {
	'country': 'SE',
	'country_code': 46,
	'locate': 'en_US',
	'timezone_offset': 2 * 3600
}
PATH_DOWNLOADS = 'downloads'
ADMIN_LIST = [id.strip() for id in os.environ.get('ADMIN_LIST','99129974').split(',')]

TG_TOKEN = os.environ.get('TG_TOKEN', '6122231504:AAEG_HvXSpu29opiJzm0Ei-aeEs9yBIttuM')
DB_USER = os.environ.get('POSTGRES_USER')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD')
DB_HOST = 'db_kot'
DB_PORT = '5432'
DB_NAME = os.environ.get('POSTGRES_DB')
if os.environ.get('DB_TYPE') == 'postgres':
	  DB_STRING = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
else:
	  DB_STRING = 'sqlite:///db.sqlite3'

LOG_LEVEL = os.getenv('LOG_LEVEL','DEBUG')
LOG_FILE = os.getenv('LOG_FILE',f'logs/{LOG_LEVEL.lower()}.log')
LOGGER_NAME = os.getenv('LOGGER_NAME','instacat')




dictConfig({
	'version': 1,
	'disable_existing_loggers': False,
	'formatters': 
		{
		'default': 
			{
			'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
			}
		},
	'handlers': 
		{
		'stdout': 
			{
			'class': 'logging.StreamHandler',
			'formatter': 'default', 
			'stream': 'ext://sys.stdout',
			},
		'file':{
			'formatter':'default',
			'class':'logging.FileHandler',
			'filename': LOG_FILE
		}
	}, 
	'loggers': 
		{
		'': 
			{                  
			'handlers': ['stdout', 'file'],    
			'level': LOG_LEVEL,    
			'propagate': True 
			}
		}
	}
)