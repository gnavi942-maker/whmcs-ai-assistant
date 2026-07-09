import pytest
from scraper.cleaner import clean_html_to_markdown, extract_meta_tags
from scraper.extractor import parse_product_page, parse_blog_page

def test_clean_html_to_markdown():
    html = """
    <html>
      <head><title>Test Title</title></head>
      <body>
        <header>Header Content</header>
        <h1>Welcome Header</h1>
        <p>This is a <strong>test paragraph</strong>.</p>
        <ul>
          <li>Feature 1</li>
          <li>Feature 2</li>
        </ul>
        <footer>Footer Content</footer>
      </body>
    </html>
    """
    cleaned = clean_html_to_markdown(html)
    assert "# Welcome Header" in cleaned
    assert "This is a test paragraph" in cleaned
    assert "* Feature 1" in cleaned
    assert "Header Content" not in cleaned
    assert "Footer Content" not in cleaned

def test_extract_meta_tags():
    html = """
    <html>
      <head>
        <title>Test Module Title</title>
        <meta name="description" content="Ultimate module integration guide" />
      </head>
      <body></body>
    </html>
    """
    meta = extract_meta_tags(html)
    assert meta["title"] == "Test Module Title"
    assert meta["description"] == "Ultimate module integration guide"

def test_parse_product_page():
    product_html = """
    <div class="product">
      <h1 class="product_title">Stripe Payment Gateway - WHMCS MODULES</h1>
      <span class="price">$49.00</span>
      <div class="woocommerce-product-details__short-description">
        <p>Short description of Stripe WHMCS module.</p>
      </div>
      <div id="tab-description">
        <p>Full description setup details.</p>
        <ul>
          <li>Easy Setup</li>
          <li>Auto Refunds</li>
        </ul>
      </div>
      <div class="product_meta">
        <span class="posted_in">Category: <a href="#">Gateways</a></span>
        <span class="tagged_as">Tags: <a href="#">Stripe</a>, <a href="#">Credit Card</a></span>
      </div>
    </div>
    """
    parsed = parse_product_page(product_html, "https://whmcsmodules.org/product/stripe-gateway/")
    assert parsed["title"] == "Stripe Payment Gateway"
    assert parsed["price_numeric"] == 49.0
    assert "Short description" in parsed["short_description"]
    assert "Gateways" in parsed["categories"]
    assert "Stripe" in parsed["tags"]
    assert parsed["features"] == ["Easy Setup", "Auto Refunds"]
