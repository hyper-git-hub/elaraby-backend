FROM python:3.8

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

RUN mkdir -p /app
WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . .

RUN cp env-dev .env

RUN ["chmod", "+x", "/app/entry-point.sh"]

EXPOSE 80

CMD ["/entry-point.sh"]
