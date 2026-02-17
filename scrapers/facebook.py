from playwright.sync_api import sync_playwright
import logging
import time
import os
import random
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
                # Use domcontentloaded for faster/more resilient loading
                page.goto(url, wait_until='domcontentloaded', timeout=45000)
                
                # Scroll down a bit
                page.evaluate("window.scrollBy(0, 1000)")
                time.sleep(5) 
                
                # Check for login wall or content
                # For groups, the feed is often in a specific role or div
                
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')
                
                # Strategy: Look for "feed" role or articles
                articles = soup.find_all('div', role='article')
                
                # Keywords indicating recent posts
                # Facebook date strings: "Yesterday at 10:00 AM", "Yesterday", "2 hrs ago", "Just now", "5 mins"
                # Chinese: "昨天", "小時", "分鐘", "剛剛"
                recent_keywords = ["Yesterday", "昨天", "hrs", "mins", "Just now", "小時", "分鐘", "剛剛"]
                
                found_count = 0
                for article in articles: 
                    text = article.get_text(separator=' | ', strip=True)
                    
                    # Check for date keywords in the text
                    is_recent = any(k in text for k in recent_keywords)
                    
                    # Debug print
                    logging.info(f"Checking post (len={len(text)}): {text[:30]}... Recent? {is_recent}")

                    if is_recent and len(text) > 20: # Lower threshold to 20
                        # clean text
                        clean_text = text.replace('|', '\n')
                        
                        posts.append({
                            'source': f"Facebook Group/Page ({name})",
                            'title': clean_text[:100] + '...', # Keep title short
                            'description': clean_text[:500] + '...', # Add longer description
                            'date': 'Recent',
                            'link': url
                        })
                        found_count += 1
                        if found_count >= 5: break # Cap at 5 relevant posts
                
            except Exception as e:
                logging.error(f"Error scraping {name}: {e}")
        
        browser.close()
    
    return posts

def scrape_personal_feed(config):
    """
    Scrapes the user's personal Facebook Feed ('Doom Scroll') for recommended content.
    """
    posts = []
    scroll_count = config['sites']['facebook'].get('scroll_count', 15)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        # Load cookies (MANDATORY for personal feed)
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        cookies_file = config['sites']['facebook'].get('cookies_file')
        if not cookies_file or not os.path.exists(cookies_file):
            logging.error("Personal Feed requires valid cookies.json!")
            return []
            
        import json
        with open(cookies_file, 'r') as f:
            cookies = json.load(f)
            
            valid_cookies = []
            for c in cookies:
                # Playwright Strictness:
                # 1. name, value, domain, path are required.
                # 2. sameSite must be compliant or omitted.
                # 3. expires/expirationDate should be handled carefully.
                
                new_cookie = {
                    'name': c.get('name'),
                    'value': c.get('value'),
                    'domain': c.get('domain'),
                    'path': c.get('path', '/')
                }
                
                if not new_cookie['name'] or not new_cookie['value'] or not new_cookie['domain']:
                    continue
                    
                # Fix Domain: ensure it works for www.facebook.com
                # If domain is .facebook.com, it should work. 
                
                if 'expirationDate' in c:
                    new_cookie['expires'] = c['expirationDate']
                elif 'expires' in c:
                    new_cookie['expires'] = c['expires']
                    
                # Simplify sameSite: Just remove it if causing issues, or strict map
                if 'sameSite' in c:
                    ss = c['sameSite'].lower()
                    if ss == 'lax': new_cookie['sameSite'] = 'Lax'
                    elif ss == 'strict': new_cookie['sameSite'] = 'Strict'
                    elif ss == 'none': new_cookie['sameSite'] = 'None'
                    # else: omit
                
                valid_cookies.append(new_cookie)
        
        if not valid_cookies:
             logging.error("No valid cookies found!")
             return []

        context = browser.new_context(**context_args)
        try:
            context.add_cookies(valid_cookies)
            logging.info(f"Loaded {len(valid_cookies)} cookies.")
        except Exception as e:
            logging.error(f"Failed to load cookies: {e}")
            return []
        page = context.new_page()
        
        url = "https://www.facebook.com/"
        logging.info(f"Doom Scrolling Personal Feed: {url} (Scrolls: {scroll_count})")
        
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=60000)
            time.sleep(5) # Wait for initial load
            
            # DEBUG: Screenshot
            page.screenshot(path="debug_facebook_login.png")
            logging.info("Saved screenshot to debug_facebook_login.png")
            
            # Doom Scroll Loop
            for i in range(scroll_count):
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                logging.info(f"Scrolling... ({i+1}/{scroll_count})")
                time.sleep(random.uniform(2, 4)) # Random delay to look human
            
            # Extract Content
            content = page.content()
            
            # DEBUG: Save HTML to inspect
            with open("facebook_feed_debug.html", "w") as f:
                f.write(content)
            logging.info("Saved debug HTML to facebook_feed_debug.html")

            soup = BeautifulSoup(content, 'html.parser')
            
            # 'div[aria-posinset]' seems more reliable for main feed
            articles = soup.select('div[role="article"], div[aria-posinset]')
            
            logging.info(f"Found {len(articles)} posts in feed (role=article or aria-posinset).")
            
            for article in articles:
                # 1. Extract Author
                author = "Unknown"
                # Authors are often in h2, h3, h4, or strong, or the first 'a' with a clear name
                author_tag = article.select_one('h2, h3, h4, strong')
                if author_tag:
                    author = author_tag.get_text(strip=True)
                
                # 2. Extract Message Content (The actual post text)
                message_text = ""
                
                # Priority 1: The explicit message container
                msg_div = article.select_one('div[data-ad-preview="message"]')
                if msg_div:
                    t = msg_div.get_text(separator=' ', strip=True)
                    if len(t) > 5:
                        message_text = t
                
                # Priority 2: Heuristic (if P1 failed)
                if not message_text:
                    candidates = article.select('div[dir="auto"], span[dir="auto"]')
                    best_text = ""
                    for c in candidates:
                        t = c.get_text(separator=' ', strip=True)
                        if len(t) > len(best_text) and "Facebook" not in t and "Like" not in t:
                            best_text = t
                    message_text = best_text
                
                if not message_text:
                    # Fallback: get all text
                    message_text = article.get_text(separator=' ', strip=True)[:500]

                clean_text = message_text
                
                # Check link (find first 'a' with href)
                # For feed posts, the timestamp link is usually the permalink
                link = ""
                
                # Try to find a link that looks like a post permalink
                # e.g. /username/posts/..., /permalink.php, /groups/...
                a_tags = article.find_all('a', href=True)
                for a in a_tags:
                    href = a['href']
                    if '/posts/' in href or '/permalink' in href or '/watch/' in href:
                        link = href
                        break
                
                # Fallback: just take the first link
                if not link and a_tags:
                    link = a_tags[0]['href']

                if link and link.startswith('/'): 
                    link = f"https://www.facebook.com{link}"
                
                if len(clean_text) > 30: # Restore threshold
                    posts.append({
                        'source': f'Personal Feed ({author})',
                        'title': clean_text[:80] + '...',
                        'description': clean_text[:2000], # Capture MORE context for AI
                        'date': 'Just Now',
                        'link': link or url
                    })
                if author_tag:
                    author = author_tag.get_text(strip=True)
                
                # Identify "Suggested for you" or similar recommendation text if possible
                
                if len(clean_text) > 30: # Lower threshold to catch shorter posts
                    posts.append({
                        'source': f'Personal Feed ({author})',
                        'title': clean_text[:80] + '...',
                        'description': clean_text[:2000], # Capture MORE context for AI
                        'date': 'Just Now',
                        'link': link or url
                    })
                    
        except Exception as e:
            logging.error(f"Error scrolling feed: {e}")
            
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
