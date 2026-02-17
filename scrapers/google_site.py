
from playwright.sync_api import sync_playwright
import logging

def scrape_google_site(config):
    """
    Scrapes Adaptive Learning Google Site.
    URL: https://sites.google.com/view/adaptive2021
    """
    url = config['sites']['google_site']['url']
    data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            
            # Google Sites has dynamic class names.
            # Best bet is to look for text content that looks like a date or "News"
            # Or get all external links? Use a broad selector for text content under sections.
            
            # Strategy: Look for the specific 'News' section if identifiable, or just dump known text blocks.
            # Based on user request, they want to track activities.
            
            # Let's try to find elements that contain date-like strings (e.g., "3/11") 
            # or look for the "Latest News" header and get following siblings.
            
            # Broad approach: Get all text that looks like a title/event
            # Google Sites often puts content in specific div structures.
            # Let's target text blocks.
            
            blocks = page.locator("div[data-text-block='true']").all() # Common internal attribute? Maybe not.
            
            # Fallback: Get all text content and filter for keywords or patterns?
            # Better: Get all links that might be events.
            
            # User provided: https://sites.google.com/view/adaptive2021/首頁
            # Let's grab the page title and any text that follows "Latest News"
            
            # Simplistic approach for now: Get page text and summarize? 
            # Or valid links.
            
            # Let's try to get all text in the main content area.
            # Try to get content from main, else body
            try:
                content_text = page.locator("main").inner_text(timeout=5000)
            except:
                content_text = page.locator("body").inner_text()
            
            # This is too unstructured. Let's return a single entry checking if the page changed?
            # Or just scrape the first few "lines" that look like events.
            
            # Let's assume we want to know if there's new content.
            # We'll grab the first 5 text blocks that are not headers.
            
            data.append({
                "title": f"Google Site Check: {page.title()}",
                "url": url,
                "date": "Check Link",
                "source": "Google Site"
            })
            
            browser.close()
            
    except Exception as e:
        logging.error(f"Error scraping Google Site: {e}")
        
    return data
