import json
import re
from bs4 import BeautifulSoup
from scraper.cleaner import clean_html_to_markdown, extract_meta_tags

def parse_product_page(html_content: str, url: str) -> dict:
    """
    Parses WooCommerce product pages specifically to extract structured metadata.
    """
    if not html_content:
        return {}

    soup = BeautifulSoup(html_content, 'html.parser')
    meta = extract_meta_tags(html_content)

    # Title
    title_el = soup.select_one('.product_title')
    title = title_el.get_text().strip() if title_el else meta.get('title', '')
    # Clean up WooCommerce suffix if any
    title = re.sub(r' - WHMCS MODULES$', '', title, flags=re.IGNORECASE).strip()

    # Price
    price_el = soup.select_one('.summary .price, .single-product .price, .price')
    price_text = ""
    price_numeric = 0.0
    if price_el:
        price_text = price_el.get_text().strip()
        # Extract number (handles e.g. "$49.00" or "$39.00 – $99.00")
        prices = re.findall(r'\d+(?:\.\d+)?', price_text)
        if prices:
            price_numeric = float(prices[-1])  # Get the final/current price

    # Short description
    short_desc_el = soup.select_one('.woocommerce-product-details__short-description')
    short_description = clean_html_to_markdown(str(short_desc_el)) if short_desc_el else ""

    # Long/Full description tab panel
    desc_el = soup.select_one('.woocommerce-Tabs-panel--description, #tab-description')
    full_description = clean_html_to_markdown(str(desc_el)) if desc_el else ""

    # Category and Tags
    meta_el = soup.select_one('.product_meta')
    categories = []
    tags = []
    if meta_el:
        cat_el = meta_el.select('.posted_in a')
        categories = [c.get_text().strip() for c in cat_el]
        tag_el = meta_el.select('.tagged_as a')
        tags = [t.get_text().strip() for t in tag_el]

    # Compatibility Info (usually matches patterns in full description like "WHMCS v8.x", "PHP 7.4/8.1", etc.)
    compatibility = []
    combined_text = f"{short_description} {full_description}"
    whmcs_versions = re.findall(r'WHMCS\s*(?:v|version)?\s*\d+\.\d+(?:\.\d+)?(?:\.x)?', combined_text, re.IGNORECASE)
    php_versions = re.findall(r'PHP\s*\d+\.\d+', combined_text, re.IGNORECASE)
    compatibility.extend(list(set(whmcs_versions + php_versions)))

    # Features (Extract bullet points or headers inside description)
    features = []
    if desc_el:
        for li in desc_el.find_all('li'):
            features.append(li.get_text().strip())
    # Fallback to lines matching checklist patterns
    if not features:
        for line in full_description.split('\n'):
            if line.startswith('*') or line.startswith('-'):
                features.append(line.replace('*', '').replace('-', '').strip())

    # FAQs (details tags or summary accordion blocks)
    faqs = []
    faq_items = soup.select('.wm-product-faq-item, details')
    for item in faq_items:
        summary = item.find('summary')
        if summary:
            question = summary.get_text().strip()
            # Clone and remove summary to get clean answer
            ans_soup = BeautifulSoup(str(item), 'html.parser')
            ans_summary = ans_soup.find('summary')
            if ans_summary:
                ans_summary.decompose()
            answer = clean_html_to_markdown(str(ans_soup)).strip()
            if question and answer:
                faqs.append({"question": question, "answer": answer})

    # Images
    images = []
    gallery = soup.select('.woocommerce-product-gallery img')
    for img in gallery:
        src = img.get('src') or img.get('data-src')
        if src and src not in images:
            images.append(src)

    # Document links
    doc_links = []
    for link in soup.select('a'):
        href = link.get('href', '')
        text = link.get_text().strip()
        if 'guide' in href or 'docs' in href or 'documentation' in href or 'setup' in href:
            doc_links.append({"text": text, "url": href})

    return {
        "title": title,
        "price_text": price_text,
        "price_numeric": price_numeric,
        "short_description": short_description,
        "full_description": full_description,
        "categories": categories,
        "tags": tags,
        "compatibility": compatibility,
        "features": features[:15], # limit to first 15 features
        "faqs": faqs,
        "images": images,
        "url": url,
        "doc_links": doc_links,
        "type": "product"
    }

def parse_blog_page(html_content: str, url: str) -> dict:
    """
    Parses WordPress blog pages / guides to extract titles, clean contents, and metadata.
    """
    if not html_content:
        return {}

    soup = BeautifulSoup(html_content, 'html.parser')
    meta = extract_meta_tags(html_content)

    title_el = soup.select_one('h1.entry-title, h1.post-title, h1')
    title = title_el.get_text().strip() if title_el else meta.get('title', '')
    title = re.sub(r' - WHMCS MODULES$', '', title, flags=re.IGNORECASE).strip()

    # Content Area
    content_el = soup.select_one('.entry-content, .post-content, article')
    content = clean_html_to_markdown(str(content_el)) if content_el else clean_html_to_markdown(html_content)

    # Category and tags
    categories = [c.get_text().strip() for c in soup.select('.cat-links a')]
    tags = [t.get_text().strip() for t in soup.select('.tags-links a')]

    return {
        "title": title,
        "content": content,
        "categories": categories,
        "tags": tags,
        "url": url,
        "type": "document"
    }

def parse_page(html_content: str, url: str) -> dict:
    """
    Detects page type and returns parsed dictionary data.
    """
    if "/product/" in url:
        return parse_product_page(html_content, url)
    else:
        # Check if the page resembles a post/guide
        return parse_blog_page(html_content, url)
