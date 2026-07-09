import pytest
from backend.app.rag.vector_store import chunk_scraped_item

def test_chunk_scraped_product():
    product_item = {
        "title": "Plex Automation Module",
        "price_text": "$59.00",
        "price_numeric": 59.0,
        "short_description": "Auto setup Plex servers.",
        "full_description": "Extremely detailed description with lots of bullet features.",
        "categories": ["Automation"],
        "features": ["Feature A", "Feature B"],
        "compatibility": ["WHMCS v8.8", "PHP 8.1"],
        "url": "https://whmcsmodules.org/product/plex/",
        "type": "product"
    }
    
    chunks = chunk_scraped_item(product_item)
    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert "Plex Automation Module" in first_chunk["text"]
    assert "Price: $59.00" in first_chunk["text"]
    assert "Feature A, Feature B" in first_chunk["text"]
    assert first_chunk["metadata"]["type"] == "product"
    assert first_chunk["metadata"]["url"] == "https://whmcsmodules.org/product/plex/"
    assert first_chunk["metadata"]["price"] == 59.0

def test_chunk_scraped_document():
    doc_item = {
        "title": "Setup Guide Modexa Theme",
        "content": "This is step 1. Upload files. Step 2. License module. Complete details.",
        "categories": ["Guide"],
        "url": "https://whmcsmodules.org/modexa-theme-setup-guide/",
        "type": "document"
    }
    
    chunks = chunk_scraped_item(doc_item)
    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert "Setup Guide Modexa Theme" in first_chunk["text"]
    assert "Upload files" in first_chunk["text"]
    assert first_chunk["metadata"]["type"] == "document"
    assert first_chunk["metadata"]["categories"] == "Guide"
