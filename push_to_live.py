
import os
import json

dev_base_dir:str = '/Volumes/Jun SSD/data'
test_base_dir:str = '/Users/junyang/church/web/data'
prod_base_dir:str = '/opt/homebrew/var/www/church/web/data'

def load_meta(base_dir:str) -> dict:
    meta_file_name:str = os.path.join(base_dir, 'config/sermon.json')
    with open(meta_file_name, 'r') as f:
        return json.load(f)

def merge_ready_sermons(ready_sermons:dict, target_sermons:dict):
    changes = []
    for dev_sermon in ready_sermons:
        item = dev_sermon['item']
        if item.startswith('2019-'):
            continue
        target_sermon = next((s for s in target_sermons if s['item'] == item), None)
        if not target_sermon:
            changes.append(dev_sermon)
            target_sermons.append(dev_sermon)
        elif  target_sermon['status'] == 'ready':
            changes.append(dev_sermon)
    return changes

def update_meta_file(base_dir:str, sermons:dict):
    meta_file_name:str = os.path.join(base_dir, 'config/sermon.json')
    with open(meta_file_name, 'w') as f:
        json.dump(sermons, f, indent=4, ensure_ascii=False)

def copy_files(changes:dict, dev_base_dir:str, target_base_dir:str):
    for dev_sermon in changes:
        item = dev_sermon['item']
        source_file = os.path.join(dev_base_dir,'script', item + '.json')
        target_file = os.path.join(target_base_dir,'script', item + '.json')
        os.system(f"rsync -u '{source_file}' '{target_file}'")

        source_file = os.path.join(dev_base_dir,'script_patched', item + '.json')
        target_file = os.path.join(target_base_dir,'script_patched', item + '.json')
        os.system(f"rsync -u '{source_file}' '{target_file}'")
        target_file = os.path.join(target_base_dir,'script_review', item + '.json')
        os.system(f"rsync -u '{source_file}' '{target_file}'")

def push(targe_base_dir:str):
    dev_sermons = load_meta(dev_base_dir)
    ready_sermons = [ dev_sermon for dev_sermon in dev_sermons if dev_sermon['status'] == 'ready']

    target_sermons = load_meta(targe_base_dir)
    changes = merge_ready_sermons(ready_sermons, target_sermons)
    if changes:
        update_meta_file(targe_base_dir, target_sermons)
        copy_files(changes, dev_base_dir, targe_base_dir)
        print(f"Pushed {len(changes)} changes to {targe_base_dir}")
    else:
        print("No changes to push")


if __name__ == '__main__':
    target = 'production'

    if target == 'test':
        push(test_base_dir)
    else:
        push(prod_base_dir)
