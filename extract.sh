sudo pybabel extract -F babel.cfg -o messages.pot --input-dirs=.
sudo pybabel update -i messages.pot -d translations
sudo pybabel compile -d translations
