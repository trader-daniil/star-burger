cp -R ./frontend /var/www/frontend
cp nginx-default.conf /etc/nginx/sites-enabled/default.conf
docker-compose -f docker-compose-prod.yaml up
systemctl restart nginx