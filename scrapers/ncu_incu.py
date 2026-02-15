
from playwright.sync_api import sync_playwright
import logging

def scrape_ncu_incu(config):
    """
    Scrapes iNCU Activity Query.
    URL: https://cis.ncu.edu.tw/iNCU/publicService/activityQuery
    """
    url = config['sites']['ncu_incu']['url']
    data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            # iNCU can be slow, giving it more time
            page.goto(url, timeout=90000)
            
            # Scroll down multiple times to load more events
            # The site might not be in chronological order, so we need to fetch more.
            for _ in range(5): # Scroll 5 times
                page.mouse.wheel(0, 3000)
                page.wait_for_timeout(1000) # Wait for load

            cards = page.locator(".card.rounded-3.my-4").all()
            
            # Increased limit since we are scrolling for more
            for card in cards[:30]: 
                try:
                    title_el = card.locator(".card-title")
                    title = title_el.inner_text().strip()
                    
                    # Link usually on the title element or a child 'a'
                    link_el = title_el.locator("a").first
                    if link_el.count() > 0:
                        href = link_el.get_attribute("href")
                        full_url = f"https://cis.ncu.edu.tw{href}" if href.startswith("/") else href
                    else:
                        full_url = url # Fallback
                        
                    # Status badge
                    badge = card.locator(".badge").first
                    status = badge.inner_text().strip() if badge.count() > 0 else "Unknown"
                    
                    data.append({
                        "title": f"[{status}] {title}",
                        "url": full_url,
                        "date": "See Details",
                        "source": "iNCU"
                    })
                except Exception as e:
                    logging.error(f"Error parsing iNCU card: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        logging.error(f"Error scraping iNCU: {e}")
        
    return data
