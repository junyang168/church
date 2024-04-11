scp -i ~/.ssh/holylogos.pem ~/church/data/script_processed/*.txt ubuntu@ec2-3-17-77-104.us-east-2.compute.amazonaws.com:/var/www/holylogos/data/script_processed
scp -i ~/.ssh/holylogos.pem ~/church/data/script/*.jsonl ubuntu@ec2-3-17-77-104.us-east-2.compute.amazonaws.com:/var/www/holylogos/data/script
scp -i ~/.ssh/holylogos.pem ~/church/data/slide/*.json ubuntu@ec2-3-17-77-104.us-east-2.compute.amazonaws.com:/var/www/holylogos/data/slide
