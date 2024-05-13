scp -i ~/Downloads/holylogos.pem ~/church/web/*.html ubuntu@ec2-3-95-17-23.compute-1.amazonaws.com:/var/www/holylogos
scp -i ~/Downloads/holylogos.pem ~/church/web/*.css ubuntu@ec2-3-95-17-23.compute-1.amazonaws.com:/var/www/holylogos
scp -i ~/Downloads/holylogos.pem ~/church/web/editor.js ubuntu@ec2-3-95-17-23.compute-1.amazonaws.com:/var/www/holylogos
scp -i ~/Downloads/holylogos.pem ~/church/web/index.js ubuntu@ec2-3-95-17-23.compute-1.amazonaws.com:/var/www/holylogos
scp -i ~/Downloads/holylogos.pem ~/church/web/signin.js ubuntu@ec2-3-95-17-23.compute-1.amazonaws.com:/var/www/holylogos
scp -i ~/Downloads/holylogos.pem ~/church/web/api/*.py ubuntu@ec2-3-95-17-23.compute-1.amazonaws.com:/var/www/holylogos/api
scp -i ~/Downloads/holylogos.pem ~/church/web/api/static/* ubuntu@ec2-3-95-17-23.compute-1.amazonaws.com:/var/www/holylogos/api/static

