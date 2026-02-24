from playwright.sync_api import sync_playwright
import logging

def scrape_ncu_club(config):
    """
    Scrapes NCU Club Official Announcements.
    """
    url = config['sites']['ncu_club']['url']
    data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            logging.info(f"Scraping NCU Club: {url}")
            page.goto(url, timeout=60000)
            
            # Selector from browser subagent: table tbody tr (skipping the first header row)
            rows = page.locator("table tbody tr").all()
            
            # Rows might include a header row, so we skip index 0
            for row in rows[1:11]: 
                try:
                    # Date: td:nth-child(2)
                    date_locator = row.locator("td:nth-child(2)")
                    if date_locator.count() == 0: continue
                    date_str = date_locator.inner_text().strip()
                    
                    # Title: td:nth-child(4)
                    title = row.locator("td:nth-child(4)").inner_text().strip()
                    if not title: continue
                    
                    # Links: td:nth-child(5) a
                    link_locator = row.locator("td:nth-child(5) a").first
                    target_url = url # Default to the page itself if no attachment
                    
                    if link_locator.count() > 0:
                        link = link_locator.get_attribute("href")
                        if link and not link.startswith("http"):
                           target_url = f"https://club.adm.ncu.edu.tw{link}"
                        elif link:
                           target_url = link

                    data.append({
                        "title": title,
                        "url": target_url,
                        "date": date_str,
                        "source": "NCU Club Announcements"
                    })
                except Exception as e:
                    logging.error(f"Error parsing NCU Club row: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        logging.error(f"Error scraping NCU Club: {e}")
        
    return data
