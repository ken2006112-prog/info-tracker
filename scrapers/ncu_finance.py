from playwright.sync_api import sync_playwright
import logging

def scrape_ncu_finance(config):
    """
    Scrapes NCU Finance Department News.
    """
    url = config['sites']['ncu_finance']['url']
    data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            logging.info(f"Scraping NCU Finance: {url}")
            page.goto(url, timeout=60000)
            
            # Selector from browser subagent: table.form_table tbody tr
            rows = page.locator("table.form_table tbody tr").all()
            
            for row in rows[:10]: # Limit to top 10
                try:
                    # Title and URL are in td:nth-child(2) a
                    link_locator = row.locator("td:nth-child(2) a")
                    if link_locator.count() > 0:
                        title = link_locator.inner_text().strip()
                        link = link_locator.get_attribute("href")
                        
                        # Date is in td:nth-child(3)
                        date_str = row.locator("td:nth-child(3)").inner_text().strip()
                        
                        target_url = link
                        if link and not link.startswith("http"):
                           # Handle relative URLs. Assuming base is fm.mgt.ncu.edu.tw
                           target_url = f"https://fm.mgt.ncu.edu.tw{link}"

                        data.append({
                            "title": title,
                            "url": target_url,
                            "date": date_str,
                            "source": "NCU Finance Department"
                        })
                except Exception as e:
                    logging.error(f"Error parsing NCU Finance row: {e}")
                    continue
            
            browser.close()
            
    except Exception as e:
        logging.error(f"Error scraping NCU Finance: {e}")
        
    return data
