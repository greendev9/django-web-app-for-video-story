FROM python:3.9.7-slim

RUN apt-get update \
&& apt-get install gcc -y \
&& apt-get clean \
&& apt-get install gunicorn3 -y \
&& apt-get install python3.9-dev -y \
&& apt-get install libcurl4-gnutls-dev librtmp-dev -y \
&& apt-get install libnss3 libnss3-dev -y \
&& apt-get install git -y \
&& apt-get install ffmpeg -y\
&& apt install redis-server -y \
&& apt install curl -y \
&& curl -sL https://deb.nodesource.com/setup_10.x \
&& apt install nodejs -y \
&& apt install npm -y
RUN touch /var/log/skigit.log
# create folders for mount
RUN mkdir /opt/static
RUN mkdir /opt/media
# set work directory
WORKDIR /opt
# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN python3 -m venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY Development_Requirements.txt /opt
#RUN python -m pip install --upgrade pip==19.3.1
RUN /opt/venv/bin/pip install -r Development_Requirements.txt
# RUN /opt/venv/bin/pip install pytest pytest-django
COPY . /opt
RUN npm install -y
# RUN python manage.py collectstatic --noinput
EXPOSE 8000
#STOPSIGNAL SIGTERM
#CMD ["python","manage.py runserver"]