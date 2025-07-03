import json
import os
from pydantic import BaseModel

# merge sermon metadata from prod into dev environments
dev_base_dir:str = '/Volumes/Jun SSD/data'
prod_base_dir:str = '/opt/homebrew/var/www/church/web/data/'
with open( dev_base_dir + '/config/sermon.json', 'r') as f:
    dev_sermons = json.load(f)
with open( prod_base_dir + '/config/sermon.json', 'r') as f:
    prod_sermons = json.load(f)

for i, dev_sermon in enumerate(dev_sermons):
    prod_sermon = next((s for s in prod_sermons if s['item'] == dev_sermon['item']), None)
    if not prod_sermon:
        continue
    dev_sermons[i] = prod_sermon

with open( dev_base_dir + '/config/sermon.json', 'w') as f:
    json.dump(dev_sermons, f, indent=4, ensure_ascii=False)
