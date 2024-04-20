set -e
git pull
export $(grep -v '^#' .env | xargs)
deploy_commit=$(git log -1 --pretty=format:%H)
/opt/star_burger/venv/bin/pip3 install -r requirements.txt
npm install
./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"
/opt/star_burger/venv/bin/python3 manage.py migrate --no-input
/opt/star_burger/venv/bin/python3 manage.py collectstatic --no-input
sudo systemctl reload nginx
sudo systemctl restart star-burger
gitrev=$(git rev-parse HEAD)
curl --request POST \
     --url https://api.rollbar.com/api/1/deploy \
     --header 'accept: application/json' \
     --header 'content-type: application/json' \
     --header 'X-Rollbar-Access-Token: '$ROLLBAR_TOKEN'' \
     --data '
{
  "environment": "production",
  "revision": "'$deploy_commit'"
}
'
echo 'You succesfullt deployed project'

