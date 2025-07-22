import os
import re
import datetime as dt
from config import DB_STRING
from sqlalchemy import create_engine, Column, Integer, Boolean, String, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import scoped_session, declarative_base, sessionmaker, relationship, Mapper
from aiogram.types import Message
import logging
logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(DB_STRING)
session = scoped_session(sessionmaker(bind=engine))
Base = declarative_base()

Base.query = session.query_property()




class TgUser(Base):
	__tablename__ = 'users'
	__tableargs__ = {
		'comment': 'Пользователи'
	}
	id = Column(Integer,nullable=False,unique=True,primary_key=True,autoincrement=True)
	tg_id = Column(Integer, comment='ID TG')
	username = Column(String(128), comment='username')
	first_name = Column(String(128), comment='Имя')
	last_name = Column(String(128), comment='Фамилия')
	messages_from = relationship("TgMessage", backref="messages_from_user", lazy="dynamic", foreign_keys='[TgMessage.from_user]')
	messages_to = relationship("TgMessage", backref="messages_to_user", lazy="dynamic", foreign_keys='[TgMessage.to_user]')
	media_files = relationship("MediaFile", backref="users_media_files", lazy="dynamic", foreign_keys='[MediaFile.user]')
	def __repr__(self):
		return f'{self.username} ({self.first_name} {self.last_name})'

class TgMessage(Base):
	__tablename__ = 'messages'
	__tableargs__ = {
		'comment': 'Сообщения телеграмм'
	}

	id = Column(Integer,nullable=False,unique=True,primary_key=True,autoincrement=True)
	from_user = Column(Integer, ForeignKey('users.id'), comment='Отправитель')
	to_user = Column(Integer, ForeignKey('users.id'), comment='Получатель')
	chat_id = Column(Integer, comment='ID чата')
	text = Column(Text, comment='Текст сообщения')
	date = Column(DateTime, comment='Время и дата')

	def __repr__(self):
		return f'{self.date}: from {self.from_user} to {self.to_user} '

class MediaFile(Base):
	__tablename__ = 'mediafiles'
	__tableargs__ = {
		'comment': 'Медиа файлы'
	}
	id = Column(Integer,nullable=False,unique=True,primary_key=True,autoincrement=True)
	filename = Column(String(255), comment='Путь до файла')
	shortcode = Column(String(128), comment='shortcode')
	user = Column(Integer, ForeignKey('users.id'), comment='Кто скачал')
	text = Column(Text, comment='Подпись')



def write_media_to_db(files:list,shortcode:str,text:str,user:TgUser,):
	for file in files:
		media_file = MediaFile(
			filename=file,
			shortcode=shortcode,
			text=text,
			user=user.id
		)
		session.add(media_file)
	session.commit()
	
def get_media_from_db(message:str):
	regex_filter_url = '(?:https?:\/\/)?(?:www.)?instagram.com\/?([a-zA-Z0-9\.\_\-]+)?\/([p]+)?([reel]+)?([tv]+)?([stories]+)?\/([a-zA-Z0-9\-\_\.]+)\/?([0-9]+)?'
	shortcode = re.split(regex_filter_url, message)[6]
	files = session.query(MediaFile).filter(MediaFile.shortcode==shortcode)
	session.commit()
	if files.count() != 0:
		return True, [f.filename for f in files], files[0].text
	else:
		return False, [], ''

def get_user(message: Message) -> TgUser:
	tg_id = message.from_user.id
	first_name = message.from_user.first_name
	last_name = message.from_user.last_name
	username = message.from_user.username
	user = session.query(TgUser).filter(TgUser.tg_id==tg_id).scalar()
	if not user:
		logger.info(f'Пользователь {username} ({first_name} {last_name}) не найден в БД')
		user = TgUser(tg_id=tg_id,
					  username=username,
					  first_name=first_name,
					  last_name=last_name)
		session.add(user)
		logger.info(f'Создан пользователь: {user}')
		session.commit()
	return user


Base.metadata.create_all(bind=engine)
self_user = session.query(TgUser).filter(TgUser.tg_id==0).scalar()
admin_user = session.query(TgUser).filter(TgUser.id==1).scalar()
if not self_user:
	self_user = TgUser(tg_id=0, username='Bot', first_name='', last_name='')
session.add(self_user)
session.commit()

def write_msg_to_db(text:str,from_user:TgUser=self_user, to_user:TgUser=self_user,chat_id:int=0):
	message = TgMessage(
		from_user=from_user.id,
		to_user=to_user.id,
		chat_id=chat_id,text=text, 
		date=dt.datetime.now()
	)
	session.add(message)
	session.commit()

def get_table_counts():
	count_users = session.query(TgUser).count()
	count_messages = session.query(TgMessage).count()
	count_media = session.query(MediaFile).count()
	return count_users, count_messages, count_media
