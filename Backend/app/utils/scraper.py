import requests
from bs4 import BeautifulSoup

def scrape_url(url: str) -> str:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    
    # Clean out non-content tags like navbars and footers
    for script_or_style in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        script_or_style.extract()

    # Extract text with space separators
    text = soup.get_text(separator=' ')
    
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text
