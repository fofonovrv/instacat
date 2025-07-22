import asyncio
import logging
from aiogram import Bot, types
from aiogram.types import Message, InputFile
from aiogram.types.input_file import FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from aiogram import Dispatcher, Router
from aiogram.filters import Command
from config import TG_TOKEN, ADMIN_LIST
from insta2 import insta_download_post
from sqlalchemy.orm import scoped_session, sessionmaker
from dbmap import engine, get_media_from_db, get_user, write_msg_to_db, self_user, admin_user, get_table_counts
import json

bot = Bot(token=TG_TOKEN)
dp = Dispatcher()
router = Router(name=__name__)
dp.include_router(router)
help_text = 'Я умею скачивать контент из Instagram. Просто пришли мне ссылку на пост/фото/видео/рилс. Я скачаю медиафайлы по ссылке и пришлю их тебе в ответ.'


logger = logging.getLogger(__name__)

@router.message(Command('start'))
async def process_start_command(message: Message):
	await bot.send_message(message.from_user.id, 'Привет! Я бот ИнстаКот.)\n' + help_text)

@router.message(Command('help'))
async def process_help_command(message: Message):
	await bot.send_message(message.from_user.id, help_text)

@router.message(Command('admin'))
async def process_admin_command(message: Message):
	if str(message.from_user.id) not in ADMIN_LIST:
		await bot.send_message(message.from_user.id, 'Вы не являетесь администратором')
	count_users, count_messages, count_media = get_table_counts()
	text = f'''
count_users = {count_users}
count_messages = {count_messages}
count_media = {count_media}
'''
	await bot.send_message(message.from_user.id, text)

@router.message()
async def text_message(msg: Message):
	user = get_user(msg)
	write_msg_to_db(msg.text, user, self_user, msg.chat.id)
	texts = []
	if 'https://www.instagram.com/' in msg.text:
		msg_text = msg.text[9:]
		incoming_msg = await bot.send_message(msg.from_user.id, 'Получил ссылку, работаю...')

		# Читаем из БД
		#get_success, media_files, text = get_media_from_db(msg_text)
		get_success = None

		if not get_success:
			download_success, media_files, text = insta_download_post(msg_text,user=user)
			logger.debug(f'Успех скачивания: {download_success}')
			logger.debug(f'Количество файлов: {len(media_files)}')
			logger.debug(json.dumps(media_files, ensure_ascii=False, indent=2))

			# Повторная попытка скачать
			# if not download_success:
			# 	await bot.send_message(msg.from_user.id, 'С первого раза не получилось, пробую снова')
			# 	download_success, media_files, text = insta_download_post(msg_text,user=user)

		if len(media_files) == 1:
			if '.mp4' in media_files[0]:
				await bot.send_video(msg.chat.id, video=FSInputFile(media_files[0]), request_timeout=120, caption='')
			elif '.jpg' in media_files[0]:
				await bot.send_photo(msg.chat.id, photo=FSInputFile(media_files[0]), request_timeout=120)
		elif len(media_files) > 1:
			media_group = MediaGroupBuilder()
			for file in media_files:
				if '.jpg' in file:
					media_group.add(type="photo", media=FSInputFile(file))
				elif '.mp4' in file:
					media_group.add(type="video", media=FSInputFile(file))
			await bot.send_media_group(msg.chat.id, media=media_group.build(), request_timeout=120)

		# Отправка текста описания частями
		# if len(text) > 4096:
		# 	for x in range(0, len(text), 4096):
		# 		texts.append(text[x:x+4096])
		# for peace_text in texts:
		# 	await bot.send_message(msg.from_user.id, peace_text)
		# await bot.delete_message(msg.chat.id, incoming_message.message_id)
		else:
			await bot.send_message(msg.from_user.id, 'Не удалось скачать. Возможно, это приватный аккаунт, либо произошла ошибка.')
		
		# if len(media_files) > 0 and text: 
		# 	await bot.send_message(msg.from_user.id, f'Описание:\n{text}')
		await incoming_msg.delete()


async def main():
	await dp.start_polling(bot)


if __name__ == '__main__':
	logger.info('Запускаем бота...')
	asyncio.run(main())
	logger.info('Бот запущен!')
					