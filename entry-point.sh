#!/bin/bash

# wait for database to get up and running
echo "Waiting for PostgreSQL to start..."
./wait-for database:5432


# Collect static files
#echo "Collect static files"
#python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Apply database migrations
#echo "installing tasks"
#python manage.py installtasks

python manage.py crontab add

service cron start

tail /var/log/cron

# Start server
#echo "Starting server"
python manage.py runserver 0.0.0.0:80
