#!/bin/bash
sudo apt-get update
sudo apt-get upgrade 
sudo apt-get install nginx
sudo ufw enable
sudo ufw allow  'Nginx HTTP'
sudo ufw allow  'Nginx HTTPS'
sudo ufw allow  'Nginx FULL'
sudo ufw allow 'OpenSSH'
sudo systemctl status nginx
nginx -t 
cp api.lionsentry.com ~/../etc/nginx/sites-available/
sudo ln -s ~/../etc/nginx/sites-available/api.lionsentry.com ~/../etc/nginx/sites-enabled/
nginx -t
sudo systemctl restart nginx
