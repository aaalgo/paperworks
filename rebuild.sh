#!/bin/bash

rm -rf db.sqlite3
rm core/migrations/0*
./manage.py makemigrations flow
./manage.py migrate
#./manage.py init
#./manage.py import_tickers
#chmod a+rw db.sqlite3
find images -type f | ./manage.py import --run
./manage.py layout --run
