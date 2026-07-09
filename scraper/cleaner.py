import re
from bs4 import BeautifulSoup

def clean_html_to_markdown(html_content: str) -> str:
    """
    Converts raw HTML into clean markdown/text by stripping headers,
    footers, scripts, styles, and returning formatted text.
    """
    if not html_content:
        return ""

    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove non-content elements
    for element in soup(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        element.decompose()

    # Convert common elements to markdown-like structures
    for header in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        level = int(header.name[1])
        header.replace_with(f"\n\n{'#' * level} {header.get_text().strip()}\n\n")

    for li in soup.find_all('li'):
        li.replace_with(f"\n* {li.get_text().strip()}")

    for p in soup.find_all('p'):
        p.replace_with(f"\n\n{p.get_text().strip()}\n\n")

    for br in soup.find_all('br'):
        br.replace_with("\n")

    for a in soup.find_all('a'):
        text = a.get_text().strip()
        href = a.get('href', '')
        if text and href:
            # Check if href is absolute or starts with site name
            if href.startswith('/') or 'whmcsmodules.org' in href:
                a.replace_with(f" [{text}]({href}) ")

    text = soup.get_text()

    # Clean up whitespace and empty lines
    text = re.sub(r'\n\s*\n', '\n\n', text)
    text = re.sub(r' +', ' ', text)
    
    # Strip leading/trailing whitespaces
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(lines)
    
    # Final cleanup of multiple empty lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()

def extract_meta_tags(html_content: str) -> dict:
    """
    Extracts title, meta description, open graph tags from raw HTML.
    """
    if not html_content:
        return {}

    soup = BeautifulSoup(html_content, 'html.parser')
    meta = {}

    title_tag = soup.find('title')
    meta['title'] = title_tag.get_text().strip() if title_tag else ""

    desc_tag = soup.find('meta', attrs={'name': 'description'}) or soup.find('meta', attrs={'property': 'og:description'})
    meta['description'] = desc_tag.get('content', '').strip() if desc_tag else ""

    # Try to extract schema/json-ld for product data
    schema_tags = soup.find_all('script', type='application/ld+json')
    meta['schemas'] = []
    for tag in schema_tags:
        try:
            import json
            data = json.loads(tag.string)
            meta['schemas'].append(data)
        except Exception:
            pass

    return meta
