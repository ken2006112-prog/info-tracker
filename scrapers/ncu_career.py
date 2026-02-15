
from playwright.sync_api import sync_playwright
import logging
import datetime

def scrape_ncu_career(config):
    """
    Scrapes NCU Career Center activities.
    URL: https://careercenter.ncu.edu.tw/activities
    """
    url = config['sites']['ncu_career']['url']
    data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            
            # The structure seems to be rows with 3 p tags: Start Date, End Date, Title
            # We target the rows
            rows = page.locator(".list-item-row").all()
            
            for row in rows[:10]: # Limit to top 10
                try:
                    # Get all p tags in this row
                    texts = row.locator("p").all_inner_texts()
                    if len(texts) >= 3:
                        date_str = texts[0].strip() # 2026-04-20 13:00
                        title = texts[2].strip() # Title
                        
                        # Get link from parent 'a' tag
                        link_element = row.locator("..") # Parent is the <a> tag
                        link = link_element.get_attribute("href")
                        
                        # Construct full URL if relative
                        target_url = link
                        if link and not link.startswith("http"):
                           target_url = f"https://careercenter.ncu.edu.tw{link}" # Or it might point to iNCU directly

                        data.append({
                            "title": title,
                            "url": target_url,
                            "date": date_str,
                            "source": "NCU Career Center"
                        })
                except Exception as e:
                    logging.error(f"Error parsing career row: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        logging.error(f"Error scraping NCU Career: {e}")
        
    return data
