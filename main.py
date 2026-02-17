
import logging
import time
import os
import yaml
import json
from datetime import datetime, timedelta

# Import custom modules
from scrapers.facebook import scrape_facebook_page
from scrapers.incu import scrape_incu, scrape_career_center
from scrapers.google_sites import scrape_adaptive_learning
from notifiers.email_sender import send_email
from notifier import send_discord_notification
from summarizer import summarize_and_format

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("job_logs.txt"),
        logging.StreamHandler()
    ]
)

def load_history():
    if os.path.exists('history.json'):
        with open('history.json', 'r') as f:
            return json.load(f)
    return []

def save_history(history):
    with open('history.json', 'w') as f:
        json.dump(history, f, indent=4)

def is_new(item, history):
    # Create a unique ID for the item
    unique_id = f"{item['date']}_{item['title']}"
    return unique_id not in history

def main():
    # 1. Load Config
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)

    all_items = []
    
    # 2. Scrape NCU Sources
    if config.get('sources', {}).get('incu_enabled', False):
        logging.info(f"Scraping NCU Club: {config['sources']['incu_url']}")
        all_items.extend(scrape_incu(config['sources']['incu_url']))
        
        logging.info(f"Scraping NCU Career: {config['sources']['career_url']}")
        all_items.extend(scrape_career_center(config['sources']['career_url']))

    if config.get('sources', {}).get('adaptive_learning_enabled', False):
         logging.info(f"Scraping Adaptive Learning: {config['sources']['adaptive_learning_url']}")
         all_items.extend(scrape_adaptive_learning(config['sources']['adaptive_learning_url']))

    # 3. Scrape KOCPC
    if config.get('kocpc', {}).get('enabled', False):
         logging.info(f"Scraping KOCPC: {config['kocpc']['url']}")
         from scrapers.kocpc import scrape_kocpc
         all_items.extend(scrape_kocpc(config['kocpc']['url']))

    # 3. Scrape Facebook Groups
    fb_pages = config.get('sources', {}).get('facebook_pages', [])
    if fb_pages:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            
            # Load cookies
            if os.path.exists('cookies.json'):
                with open('cookies.json', 'r') as f:
                    cookies = json.load(f)
                    context.add_cookies(cookies)
                    logging.info(f"Loaded {len(cookies)} valid cookies out of 3.")
            
            page = context.new_page()
            
            for fb_name, fb_url in fb_pages.items():
                if fb_url:
                    logging.info(f"Scraping Facebook: {fb_name} ({fb_url})")
                    try:
                        fb_items = scrape_facebook_page(page, fb_url, fb_name)
                        all_items.extend(fb_items)
                        time.sleep(2) # Polite delay
                    except Exception as e:
                        logging.error(f"Error scraping {fb_name}: {e}")
            
                    except Exception as e:
                        logging.error(f"Error scraping {fb_name}: {e}")
            
            browser.close()

    # 3.5 Personal Feed "Doom Scroll"
    if config['sites'].get('facebook', {}).get('feed_enabled', False):
        from scrapers.facebook import scrape_personal_feed
        logging.info("Starting Personal Feed Doom Scroll...")
        feed_items = scrape_personal_feed(config)
        all_items.extend(feed_items)

    # 4. Filter New Items
    history = load_history()
    new_items = []
    
    for item in all_items:
        if is_new(item, history):
            new_items.append(item)
            # Add to history immediately to prevent dupes in same run
            history.append(f"{item['date']}_{item['title']}")
            
    logging.info(f"Total items scraped: {len(all_items)}")
    logging.info(f"New items to report: {len(new_items)}")
    
    if not new_items:
        logging.info("No new items found. Skipping email.")
        return

    # --- Refactored: Group First, then Summarize Source ---
    grouped_data = {}
    
    # 1. Group items by source
    for item in new_items:
        source = item.get('source', 'Unknown')
        if source not in grouped_data:
            grouped_data[source] = {'items': [], 'summary': None}
        grouped_data[source]['items'].append(item)
        
    # 2. AI Processing (Per Source)
    if config.get('ai', {}).get('enabled', False):
        logging.info("AI Summarization enabled. Processing per source...")
        from ai_helper import summarize_group
        
        for source, data in grouped_data.items():
            logging.info(f"Summarizing source: {source} ({len(data['items'])} items)")
            try:
                summary = summarize_group(source, data['items'], config)
                if summary:
                    data['summary'] = summary
                
                # Rate Limit Protection (free tier)
                time.sleep(10) 
            except Exception as e:
                logging.error(f"Error summarizing {source}: {e}")

    # 5. Summarize (Generate Report)
    report_html = summarize_and_format(grouped_data)
    
    # 6. Send Notifications
    today = datetime.now().strftime('%Y-%m-%d')
    subject = f"Info Tracker Daily Report - {today} ({len(new_items)} new)"

    # Send Email if enabled
    if config.get('email', {}).get('enabled', False):
        logging.info(f"Sending email to {config['email']['recipient']}...")
        send_email(config, subject, report_html)
        logging.info("Email sent successfully.")

    # Send Discord if enabled
    if config.get('discord', {}).get('enabled', False):
        webhook_url = config.get('discord', {}).get('webhook_url')
        if webhook_url:
            send_discord_notification(webhook_url, f"**{subject}**\n\nCheck your email for the full report.")
        else:
            logging.warning("Discord enabled but no webhook URL provided.")

    # 7. Save History
    save_history(history)

if __name__ == "__main__":
    main()
