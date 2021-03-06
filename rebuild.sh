#!/bin/bash

mkdir -p jobs embed aligned
rm -rf db.sqlite3
rm flow/migrations/0*
./manage.py makemigrations flow
./manage.py migrate
find images -type f | shuf |  ./manage.py import --run
./manage.py pack --run
./manage.py gen_tasks --run
