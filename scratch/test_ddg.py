import requests
import re
from urllib.parse import unquote

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}
r = requests.get('https://html.duckduckgo.com/html/?q=headphones+site:unsplash.com', headers=headers)
print("Status:", r.status_code)
links = re.findall(r'href="/html/\?uddg=([^"]+)"', r.text)
for link in links:
    decoded = unquote(link)
    if 'unsplash.com/photo-' in decoded:
        print("Found:", decoded)
