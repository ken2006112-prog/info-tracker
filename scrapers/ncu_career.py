
from playwright.sync_api import sync_playwright
import logging
import datetime

def scrape_ncu_career(config):
    """
    Scrapes NCU Career Center activities.
    URL: https://careercenter.ncu.edu.tw/activities
    """
    # Handle both single URL (old config) and list of URLs (new config)
    urls = config['sites']['ncu_career'].get('urls', [config['sites']['ncu_career'].get('url')])
    data = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()
            
            for url in urls:
                if not url: continue
                logging.info(f"Scraping NCU Career: {url}")
                page.goto(url, timeout=60000)
                
                rows = page.locator(".list-item-row").all()
                for row in rows[:10]: # Limit to top 10 per page
                    try:
                        texts = row.locator("p").all_inner_texts()
                        if len(texts) >= 3:
                            date_str = texts[0].strip()
                            # Use URL path to determine text structure precisely
                            url_path = url.split('/')[-1]
                            
                            if url_path == 'activities':
                                # activities: Start Date [0], End Date [1], Title [2]
                                title = texts[2].strip().split('\n')[0] if len(texts) > 2 else "No Title"
                            else:
                                # news, extra-event, internship: Post Date [0], Title [1], Clicks [2]
                                title = texts[1].strip().split('\n')[0] if len(texts) > 1 else "No Title"
                                
                            link_element = row.locator("..") # Parent is the <a> tag
                            link = link_element.get_attribute("href")
                            
                            target_url = link
                            if link and not link.startswith("http"):
                               target_url = f"https://careercenter.ncu.edu.tw{link}"
    
                            data.append({
                                "title": title,
                                "url": target_url,
                                "date": date_str,
                                "source": f"NCU Career Center ({url.split('/')[-1]})"
                            })
                    except Exception as e:
                        logging.error(f"Error parsing career row: {e}")
                        continue
            
            browser.close()
            
    except Exception as e:
        logging.error(f"Error scraping NCU Career: {e}")
        
    return data
