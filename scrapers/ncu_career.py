
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
                            # Distinguish between Activity (Start, End, Title) and News (Date, Title, Clicks)
                            title = texts[2].strip() 
                            if "點閱" in title or title.isdigit() or len(texts[-1]) < 15:
                                title = texts[1].strip()
                                
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
