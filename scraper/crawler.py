import time
import requests
import xml.etree.ElementTree as ET
import logging
from typing import List, Dict
from bs4 import BeautifulSoup
from scraper.extractor import parse_page

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5'
}

def get_xml_sitemap_urls(sitemap_url: str) -> List[str]:
    """
    Parses a sitemap XML or sitemap index XML to find links.
    """
    urls = []
    try:
        response = requests.get(sitemap_url, headers=HEADERS, timeout=15, verify=True)
        if response.status_code != 200:
            logger.error(f"Failed to fetch sitemap {sitemap_url}: status {response.status_code}")
            return urls
        
        # Parse XML using ElementTree
        root = ET.fromstring(response.content)
        
        # Handle namespaces
        namespace = ''
        if root.tag.startswith('{'):
            namespace = root.tag.split('}')[0] + '}'
            
        # Check if it's a sitemap index or urlset
        if 'sitemapindex' in root.tag:
            for sitemap in root.findall(f'.//{namespace}sitemap'):
                loc = sitemap.find(f'{namespace}loc')
                if loc is not None and loc.text:
                    sub_urls = get_xml_sitemap_urls(loc.text)
                    urls.extend(sub_urls)
        elif 'urlset' in root.tag:
            for url_node in root.findall(f'.//{namespace}url'):
                loc = url_node.find(f'{namespace}loc')
                if loc is not None and loc.text:
                    urls.append(loc.text)
    except Exception as e:
        logger.error(f"Error reading sitemap {sitemap_url}: {e}")
        
    return list(set(urls))

def crawl_site(target_url: str, crawl_delay: float = 1.0) -> List[Dict]:
    """
    Crawls the entire site by fetching its sitemap, parsing all products and articles,
    and returns a list of structured dictionaries.
    """
    logger.info(f"Starting crawl for target website: {target_url}")
    
    # Try XML sitemap first
    sitemap_index = f"{target_url.rstrip('/')}/sitemap.xml"
    urls = get_xml_sitemap_urls(sitemap_index)
    
    # Fallbacks if sitemap parsing failed
    if not urls:
        logger.warning("XML Sitemap empty or failed to parse. Falling back to homepage scanning...")
        urls = [
            target_url,
            f"{target_url.rstrip('/')}/products/",
            f"{target_url.rstrip('/')}/product/modexa-whmcs-theme/",
            f"{target_url.rstrip('/')}/product/plex-automation-for-whmcs/",
            f"{target_url.rstrip('/')}/product/dream4k-reseller-module-for-whmcs/",
            f"{target_url.rstrip('/')}/product/tv-plus-reseller-module-for-whmcs/",
            f"{target_url.rstrip('/')}/product/golden-ott-reseller-module-for-whmcs/",
            f"{target_url.rstrip('/')}/product/activation-reseller-module-for-whmcs/",
            f"{target_url.rstrip('/')}/nxt-dash-whmcs-module-full-installation-and-configuration-guide-2026/",
            f"{target_url.rstrip('/')}/ott-master-panel-for-whmcs-complete-setup-guide-for-iptv-resellers-2026/"
        ]

    # Filter URLs to products, guides, and articles we care about (ignore cart, my-account, checkout, feeds, tags, categories)
    filtered_urls = []
    for url in urls:
        if any(ignored in url for ignored in ['/cart/', '/checkout/', '/my-account/', '/feed/', '/tag/', '/category/', 'xmlrpc']):
            continue
        filtered_urls.append(url)

    logger.info(f"Discovered {len(filtered_urls)} URLs to crawl.")
    
    scraped_data = []
    for index, url in enumerate(filtered_urls):
        logger.info(f"[{index+1}/{len(filtered_urls)}] Fetching: {url}")
        try:
            # Add delay to avoid hammering server
            time.sleep(crawl_delay)
            
            response = requests.get(url, headers=HEADERS, timeout=15)
            if response.status_code != 200:
                logger.error(f"Failed to fetch {url}: status {response.status_code}")
                continue
                
            parsed_data = parse_page(response.text, url)
            if parsed_data:
                scraped_data.append(parsed_data)
                logger.info(f"Successfully scraped: {parsed_data.get('title') or url}")
        except Exception as e:
            logger.error(f"Exception while scraping {url}: {e}")

    logger.info(f"Crawl finished. Scraped {len(scraped_data)} successful documents.")
    return scraped_data

if __name__ == '__main__':
    # Test run
    data = crawl_site("https://whmcsmodules.org/")
    import json
    with open("scraped_test.json", "w") as f:
        json.dump(data, f, indent=2)
    print("Done")
