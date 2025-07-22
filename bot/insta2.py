from instagrapi import Client
from config import INSTA_USER, INSTA_PASSWORD, INSTA_SESSION, PATH_DOWNLOADS, INSTA_LOCATE
import logging
import datetime as dt
import re
import os
from pathlib import Path
from sqlalchemy.orm import scoped_session, sessionmaker
from dbmap import write_media_to_db, TgUser, self_user
import urllib.request
from typing import Tuple, List
import httpx
import time

logger = logging.getLogger(__name__)

# Инициализируем клиент один раз
cl: Client = None


def configure_client(cl: Client) -> Client:
    """
    Настраивает дополнительные параметры клиента
    """

    # Параметры местоположения клиента
    cl.set_country = INSTA_LOCATE.get('country', 'US')
    cl.set_country_code = INSTA_LOCATE.get('country_code', 1)
    cl.set_locale = INSTA_LOCATE.get('locale', 'en_US')
    cl.set_timezone_offset = INSTA_LOCATE.get('timezone_offset', 14400)

    # Задержки между скачиваниями
    cl.delay_range = [1, 3]

    # Увеличим таймаут
    cl.request_timeout = 1

    # Вроде бы прибавляет приватные куки к публичным запросам
    cl.inject_sessionid_to_public()


def init_client() -> bool:
    """
    Инициализирует и логинит клиента instagrapi. Если сессия сохранена — использует её.
    Иначе логинится вручную и сохраняет сессию в файл.
    """
    global cl
    if cl is None:
        cl = Client()
        if os.path.exists(INSTA_SESSION):
            try:
                cl.load_settings(INSTA_SESSION)
                # Пробуем вызвать метод, требующий авторизации, чтобы убедиться, что сессия валидна
                cl.get_timeline_feed()
                logger.debug(f'Текущая сессия из файла валидна')
                cl = configure_client(cl)
                return  True
            except Exception as e:
                logger.warning(f'[init_client] Сохранённая сессия недействительна: {e}')

        # Файл не найден или сессия невалидна — логинимся вручную
        cl.login(INSTA_USER, INSTA_PASSWORD)
        cl = configure_client(cl)
        cl.dump_settings(INSTA_SESSION)
        logger.info('Залогинились успешно!')
        return True


regex_filter_url = r'(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:[a-zA-Z0-9\._\-]+)?\/?(?:p|reel|tv|stories)?\/([a-zA-Z0-9\-_\.]+)\/?'


def insta_download_post(
    message: str,
    user: TgUser = self_user
) -> Tuple[bool, List[str], str]:
    """
    Скачивает пост Instagram (фото, видео, reels, альбом) по ссылке.

    :param message: Сообщение или ссылка с кодом поста Instagram.
    :param user: Пользователь Telegram (для записи в БД).
    :return: Кортеж (успешность, список файлов, подпись/ошибка).
    """
    start_time = time.time()
    try:
        path = Path(PATH_DOWNLOADS, dt.datetime.now().strftime('%d-%m-%Y'))
        init_client()
        match = re.search(regex_filter_url, message)
        if not match:
            return False, [], 'Не удалось извлечь код из ссылки'

        shortcode = match.group(1)
        media_url = f'https://www.instagram.com/p/{shortcode}/'
        # media_pk = cl.media_pk_from_url(media_url)
        logger.debug(f'Получчение media info')
        media_pk = cl.media_pk_from_code(shortcode)

        # media = cl.media_oembed(media_url)  # Сокращенный вариант, без media_type
        # media_pk = media.media_id.split('_')[0]

        # media = cl.media_info(media_pk)
        media = cl.media_info_v1(media_pk)
        # media = cl.media_info_a1(media_pk)
        # media = cl.media_info_gql(media_pk)
        logger.debug(f'Media info получено')

        folder = Path(path, shortcode)
        folder.mkdir(parents=True, exist_ok=True)

        downloaded_files: List[Path] = []

        # Для полного media
        caption = media.caption_text or ''

        # Для сокращенного media_oembed
        # caption = media.title or ''

        if media.media_type == 1:  # Фото
            logger.debug(f'Скачиваем фото')
            file_path = cl.photo_download(media_pk, folder)
            downloaded_files.append(file_path)

        elif media.media_type == 2:  # Видео / Reel / IGTV
            logger.debug(f'Скачиваем видео/рилс')
            # file_path = cl.video_download(media_pk, folder)
            file_path = cl.photo_download_by_url(media_pk, media_pk, folder)
            downloaded_files.append(file_path)

        elif media.media_type == 8:  # Альбом
            logger.debug(f'Скачиваем альбом')
            for item in media.resources:
                if item.media_type == 1:
                    logger.debug(f'Скачиваем фото')
                    file_path = cl.photo_download(item.pk, folder)
                    downloaded_files.append(file_path)
                elif item.media_type == 2:
                    logger.debug(f'Скачиваем видео/рилс')
                    # file_path = cl.video_download(item.pk, folder)
                    file_path = cl.photo_download_by_url(media_pk, media_pk, folder)
                    downloaded_files.append(file_path)

        file_paths = [str(p.resolve()) for p in downloaded_files]
        write_media_to_db(file_paths, shortcode, caption, user)
        end_time = time.time()
        logger.debug(f"Время скачивания: {end_time - start_time:.4f} секунд")
        return True, file_paths, caption

    except Exception as error:
        logger.error(f'Ошибка insta_download_post: {str(error)}')
        return False, [], 'Ошибка: ' + str(error)