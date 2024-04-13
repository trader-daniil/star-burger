set -e
git pull
sudo systemctl status nginx
sudo systemctl status star-burger
/opt/star_burger/venv/bin/pip3 install -r requirements.txt
npm ci --dev
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
/opt/star_burger/venv/bin/python3 manage.py migrate
/opt/star_burger/venv/bin/python3 manage.py collectstatic
sudo systemctl restart nginx
sudo systemctl restart star-burger
echo "You successfully deployed project"