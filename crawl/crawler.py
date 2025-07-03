import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
import re
from charset_normalizer import detect
import json

base_dir = '/Volumes/Jun SSD/data'

def get_page_encoding(response):
    """Detect the encoding of the HTML response."""
    # Check Content-Type header
    content_type = response.headers.get('content-type', '')
    if 'charset=' in content_type.lower():
        charset = content_type.split('charset=')[-1].strip()
        return charset

    # Check HTML meta tags
    soup = BeautifulSoup(response.content, 'html.parser')
    meta = soup.find('meta', charset=True)
    if meta and meta.get('charset'):
        return meta['charset']

    meta = soup.find('meta', attrs={'http-equiv': 'Content-Type'})
    if meta and meta.get('content'):
        content = meta['content'].lower()
        if 'charset=' in content:
            return content.split('charset=')[-1].strip()

    # Fallback: Detect encoding from content
    result = detect(response.content)
    if result['encoding']:
        return result['encoding']

    # Default to UTF-8 if all else fails
    return 'utf-8'

def is_valid_url(url):
    """Check if a URL is valid."""
    try:
        result = requests.head(url, allow_redirects=True, timeout=5)
        return result.status_code == 200
    except requests.RequestException:
        return False

def get_audio_url_from_ram(ram_url):
    """Extract audio file URL from a .ram file."""
    try:
        response = requests.get(ram_url, timeout=10)
        response.raise_for_status()
        # .ram files typically contain a single URL
        audio_url = response.text.strip()
        if audio_url and is_valid_url(audio_url):
            return audio_url
        return None
    except requests.RequestException as e:
        print(f"Error fetching .ram file {ram_url}: {e}")
        return None

def download_audio(audio_url, output_dir, filename):
    """Download the audio file to the specified directory."""
    try:
        response = requests.get(audio_url, timeout=10, stream=True)
        response.raise_for_status()
        
        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Sanitize filename
        filename = re.sub(r'[^\w\-_\. ]', '_', filename)
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"Downloaded: {filepath}")
    except requests.RequestException as e:
        print(f"Error downloading {audio_url}: {e}")

def update_metadata(ram_links):
    with open(base_dir + '/config/sermon.json', 'r') as f:
        sermons = json.load(f)
    for title, item, ram_url in ram_links:
        sermon = next((s for s in sermons if s['item'] == item), None)
        if not sermon:
            sermons.append({
                'item': item,
                'title': title,
                'status': 'in development',
            })
    with open(base_dir + '/config/sermon.json', 'w') as f:
        json.dump(sermons, f, indent=4, ensure_ascii=False)

def crawl_and_download_ram(url, output_dir="audio_files"):
    """Crawl a webpage for .ram links and download their audio files."""
    try:
        # Fetch the webpage
        response = requests.get(url)
        response.raise_for_status()

        encoding = get_page_encoding(response)
        response.encoding = encoding  # Set the encoding explicitly
        print(f"Detected encoding: {encoding}")
        
        # Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        # Filter for .ram files
        ram_links = [(link.text.split(' ')[0], link['href']) for link in links if link['href'].lower().endswith('.ram')]
        
        if not ram_links:
            print("No .ram links found on the page.")
            return
        
        # Resolve relative URLs
        base_url = urllib.parse.urljoin(url, '.')
        ram_links = [
            (title, link[:-len('.ram')], urllib.parse.urljoin(base_url, link) if not link.startswith('http') else link)
            for title, link in ram_links
        ]

        # Update metadata
        update_metadata(ram_links)
        
        # Process each .ram link
        for title, item, ram_url in ram_links:
            print(f"Processing .ram file: {ram_url}")
            audio_url = get_audio_url_from_ram(ram_url)
            if audio_url:
                # Generate a filename from the audio URL
                filename = item + '.rm'
                download_audio(audio_url, output_dir, filename)
            else:
                print(f"No valid audio URL found in {ram_url}")               
    except requests.RequestException as e:
        print(f"Error crawling {url}: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")
    

# Example usage
if __name__ == "__main__":
    target_url = "http://www.gtl.org/426/426.html"  # Replace with the target webpage URL
    crawl_and_download_ram(target_url, output_dir=base_dir + '/audio')