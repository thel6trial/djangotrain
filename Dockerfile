FROM python:3.11.1-alpine
RUN apk update && apk add --no-cache \
    curl \
    bash \
    gcc \
    libc-dev \
    libffi-dev \
    mariadb-dev \
    python3-dev

WORKDIR /var/www

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
# ENV MYSQLCLIENT_CFLAGS="-I/usr/include/mysql"
# ENV MYSQLCLIENT_LDFLAGS="-L/usr/lib/mysql"

RUN pip install --upgrade pip
RUN pip install --upgrade setuptools
RUN pip install mysqlclient
RUN pip install Django==4.2.1
# mysqlclient==2.2.1
RUN pip install django-ckeditor==6.7.0
RUN pip install channels==4.0.0
RUN pip install daphne==4.0.0
RUN pip install django-guardian==2.4.0
RUN pip install django-role-permissions==3.2.0
RUN pip install Pillow==9.2.0
RUN pip install redis==5.0.1
RUN pip install celery==5.3.6
RUN pip install Faker==22.6.0
RUN pip install django-htmx==1.17.2
RUN pip install uvicorn
RUN pip install PyJWT==2.8.0 
RUN pip install python3-openid==3.2.0 
RUN pip install social-auth-app-django==5.4.0 
RUN pip install social-auth-core==4.5.3
RUN pip install django-allauth==0.61.1
RUN pip install google-auth 
RUN pip install google-auth-oauthlib
RUN pip install google-auth-httplib2==0.2.0
RUN pip install httplib2==0.22.0
RUN pip install requests
RUN pip install google-api-python-client
RUN pip install python-twitter
RUN pip install line-bot-sdk
RUN pip install jwt==1.3.1
RUN pip install 'uvicorn[standard]'
COPY ./static/blog/images/images .var/www/static/blog/images/images
COPY . /var/www/
#RUN pip install -r requirements.txt
