FROM python:3.11-slim

ENV PYTHONFAULTHANDLER=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONHASHSEED=random
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_NO_CACHE_DIR=off
ENV PIP_DISABLE_PIP_VERSION_CHECK=on
ENV PIP_DEFAULT_TIMEOUT=100

RUN mkdir /bot
WORKDIR /bot
COPY . .

RUN apt-get update && apt install -y python3 python3-pip python3-dev build-essential python3-venv && pip3 install -r requirements.txt

CMD ["python3", "/bot/bot.py"]
