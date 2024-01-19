import os
from logging.config import dictConfig
from logging import getLogger

# BASE_DIR = Path(__file__).resolve().parent.parent
INSTA_USER = 'catinstabot'
INSTA_PASSWORD = 'papasong3'
INSTA_SESSION = 'session-kot_insta_bot'
PATH_DOWNLOADS = 'downloads'

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

def init_logging(log_file, log_level, logger_name):
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
				'filename': log_file
			}
		}, 
		'loggers': 
			{
			'': 
				{                  
				'handlers': ['stdout', 'file'],    
				'level': log_level,    
				'propagate': True 
				}
			}
		}
	)
	return getLogger(logger_name)

logger = init_logging(LOG_FILE, LOG_LEVEL, LOGGER_NAME)