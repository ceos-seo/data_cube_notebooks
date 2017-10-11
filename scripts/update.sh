rm -rf apps/*/migrations/0*.py
python manage.py dumpdata auth.user > users.json

psql -U dc_user datacube -c "DROP SCHEMA public CASCADE;"
psql -U dc_user datacube -c "CREATE SCHEMA public;"

bash scripts/initial_migrations.sh
python manage.py loaddata users.json

rm users.json

sudo service apache2 restart
sudo /etc/init.d/data_cube_ui restart
sudo /etc/init.d/celerybeat restart
