from playwright.sync_api import sync_playwright
import logging
import time
import os
from bs4 import BeautifulSoup

def scrape_facebook_page(config):
    """
    Scrapes a public Facebook page OR Group for the latest post.
    """
    pages_list = config['sites']['facebook']['pages']
    
    posts = []
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        
        # Load cookies if available
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        # Check for cookies file in config
        cookies_file = config['sites']['facebook'].get('cookies_file')
        if cookies_file and os.path.exists(cookies_file):
            import json
            with open(cookies_file, 'r') as f:
                cookies = json.load(f)
                # Fix for Playwright: sameSite must be Strict, Lax, or None. 
                # Extensions often export 'no_restriction' or lowercase 'none'.
                for c in cookies:
                    if 'sameSite' in c:
                        val = c['sameSite'].lower()
                        if val == 'no_restriction' or val == 'unspecified':
                            c['sameSite'] = 'None'
                        elif val == 'lax':
                            c['sameSite'] = 'Lax'
                        elif val == 'strict':
                            c['sameSite'] = 'Strict'
                        elif val == 'none':
                            c['sameSite'] = 'None'
                
                # Filter out cookies without domain or path (Playwright requirement)
                valid_cookies = [c for c in cookies if 'domain' in c and 'path' in c and 'name' in c and 'value' in c]
                logging.info(f"Loaded {len(valid_cookies)} valid cookies out of {len(cookies)}.")
                
                if valid_cookies:
                    context = browser.new_context(**context_args)
                    context.add_cookies(valid_cookies)
                else:
                    logging.warning("No valid cookies found in file. Proceeding without cookies.")
                    context = browser.new_context(**context_args)
        else:
            logging.info("No cookies found. Scraper might be limited to Public Pages only.")
            context = browser.new_context(**context_args)
            
        page = context.new_page()
        
        for item in pages_list:
            url = item['url']
            name = item.get('name', 'Facebook')
            
            logging.info(f"Scraping Facebook: {name} ({url})")
            
            try:
                page.goto(url, wait_until='networkidle', timeout=60000)
                
                # Scroll down a bit
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(5) 
                
                # Check for login wall or content
                # For groups, the feed is often in a specific role or div
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Strategy: Look for "feed" role or articles
                articles = soup.find_all('div', role='article')
                
                # Keywords indicating "Yesterday"
                # Facebook date strings: "Yesterday at 10:00 AM", "昨天 10:00", "2 hrs ago" (Today), "July 20" (Older)
                # If we want strictly yesterday: look for "Yesterday" or "昨天"
                # If we want "Since last run" (approx 24h), we might include "hrs ago" if we run daily.
                # But user asked strictly for "posted yesterday".
                yesterday_keywords = ["Yesterday", "昨天"]
                
                found_count = 0
                for article in articles: 
                    text = article.get_text(separator=' | ', strip=True)
                    
                    # Check for date keywords in the text
                    # specific implementations might hide date in a nested span/aria-label not easily scraped by get_text
                    # But often it's visible.
                    
                    is_yesterday = any(k in text for k in yesterday_keywords)
                    
                    # Debug: print dates found if needed
                    # logging.info(f"Article text sample: {text[:50]}...")

                    if is_yesterday and len(text) > 30:
                        posts.append({
                            'source': f"Facebook Group/Page ({name})",
                            'title': text[:100] + '...',
                            'date': 'Yesterday',
                            'link': url
                        })
                        found_count += 1
                        if found_count >= 5: break # Cap at 5 relevant posts
                
            except Exception as e:
                logging.error(f"Error scraping {name}: {e}")
        
        browser.close()
    
    return posts

if __name__ == "__main__":
     # Test with specific page
    config = {
        'sites': {
            'facebook': {
                'pages': [{'url': 'https://www.facebook.com/groups/OpenAI.ChatGPT.TW/', 'name': 'Test Group'}],
                'cookies_file': 'cookies.json'
            }
        }
    }
    print(scrape_facebook_page(config))
