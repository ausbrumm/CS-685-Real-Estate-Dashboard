import requests
from bs4 import BeautifulSoup

page_url = "https://www.realestatedataset.com/download/us/for-sale/"

# get the HTML of the page
r = requests.get(page_url)
r.raise_for_status()

soup = BeautifulSoup(r.text, "html.parser")

# find the download link (usually an <a> with 'download' or '.csv')
download_link = None
for a in soup.find_all("a", href=True):
    if "csv" in a["href"]:
        download_link = a["href"]
        break

if download_link is None:
    raise ValueError("No CSV download link found on the page")

# handle relative links
if download_link.startswith("/"):
    from urllib.parse import urljoin
    download_link = urljoin(page_url, download_link)

print("Download URL:", download_link)

# now read just the first few lines
with requests.get(download_link, stream=True) as r:
    r.raise_for_status()
    for i, line in enumerate(r.iter_lines(decode_unicode=True)):
        if i >= 5:  # header + 4 rows
            break
        print(line)
