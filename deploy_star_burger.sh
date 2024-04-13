set -e
git pull
sudo systemctl status nginx
sudo systemctl status star-burger
/opt/star_burger/venv/bin/pip3 install -r requirements.txt
npm install
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
/opt/star_burger/venv/bin/python3 manage.py migrate
/opt/star_burger/venv/bin/python3 manage.py collectstatic
sudo systemctl restart nginx
sudo systemctl restart star-burger
gitrev=$(git rev-parse HEAD)
curl --request POST \
     --url https://api.rollbar.com/api/1/deploy \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --header 'X-Rollbar-Access-Token: ' \
     --data '
{
  "environment": "production",
  "revision": "'$gitrev'"
}
'
echo 'You succesfullt deployed project'

