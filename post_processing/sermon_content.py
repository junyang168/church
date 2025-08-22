import requests
import xml.etree.ElementTree as ET
import os
import json

class SermonContent:

    def get_sitemap_urls(self):
        sitemap_url = f"{self.base_url}/public/sitemap"
        response = requests.get(sitemap_url)
        if response.status_code == 200:
            sitemap_data = response.text
            urls = self.parse_sitemap(sitemap_data)
            return urls
        else:
            return []

    def parse_sitemap(self, sitemap_data):
        root = ET.fromstring(sitemap_data)
        urls = []
        for url in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc = url.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc').text
            urls.append(loc)
        return urls

    def get_item(self, url, is_published:bool = False):
        item_name = url.split('/')[-1]
        response = requests.get(f"{self.base_url}/sc_api/final_sermon/junyang168@gmail.com/{item_name}")
        if response.status_code == 200:
            sermon_data = response.json()
            sermon_data['metadata']['item'] = item_name
            return sermon_data
        else:
            return None   

    def __init__(self):         
        self.base_url = os.getenv('SERMON_BASE_URL')
        self.base_dir = '/Users/junyang/church/web/data/sermon_content'

    def get_source(self) -> str:
        return "holylogos"
    
    def get_content(self, save_data = False) -> list[dict]:
        item_urls = self.get_sitemap_urls()
        data = []
        for url in item_urls:
            article_data = self.get_item(url)
            data.append(article_data)
            if save_data:
                with open(f"{self.base_dir}/{url.split('/')[-1]}.json", 'w') as f:
                    json.dump(article_data, f, ensure_ascii=False, indent=2)
        return data

if __name__ == '__main__':
    sc = SermonContent()
    content = sc.get_content(True)

