From python:3.8.5

WORKDIR /home/

RUN echo "testing"

RUN git clone https://github.com/wkddnjswns3793/pragmaticEmo.git

WORKDIR /home/pragmaticEmo/

RUN pip3 install -vvv --no-cache-dir -r requirements.txt

RUN pip3 install gunicorn

RUN pip3 install mysqlclient

RUN apt-get update && apt-get install -y python3-opencv

RUN pip install opencv-python

RUN echo "SECRET_KEY=3#+t!lv&*#c2ykt)!$b1%equ(($l6gzvzi$8r$+lpboo+%z+e*" > .env

RUN python3 manage.py collectstatic

EXPOSE 8000

CMD ["bash", "-c", "python3 manage.py migrate --settings=pragmatic.settings.deploy && gunicorn pragmatic.wsgi --env DJANGO_SETTINGS_MODULE=pragmatic.settings.deploy --bind 0.0.0.0:8000"]