FROM python:3.8.2-slim

WORKDIR /src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONBUFFERED 1

RUN apt-get install \
    default-jre \
    python-pygame

RUN pip install --upgrade pip
RUN pip install git+https://github.com/e9t/PyTagCloud.git
COPY ./requirements.txt /src/app/requirements.txt
RUN pip install -r requirements.txt

COPY . /src/app

CMD [gunicorn, --bind, 0.0.0.0:5000, app:app]