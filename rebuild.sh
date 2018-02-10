#!/bin/bash

rm -rf db.sqlite3
rm flow/migrations/0*
./manage.py makemigrations flow
./manage.py migrate
find images -type f | ./manage.py import --run
./manage.py pack --run
./manage.py gen_jobs --run
