
import logging
import time
import os
import yaml
import json
from datetime import datetime, timedelta

# Import custom modules
from scrapers.facebook import scrape_facebook_page
from scrapers.ncu_incu import scrape_ncu_incu
from scrapers.ncu_career import scrape_ncu_career
from scrapers.google_site import scrape_google_site
from scrapers.ncu_finance import scrape_ncu_finance
from scrapers.ncu_club import scrape_ncu_club
from notifier import send_email, send_discord_webhook
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
    error_log = []
    
    # 2. Scrape NCU Sources
    sites = config.get('sites', {})
    
    if sites.get('ncu_club', {}).get('enabled', False):
        try:
            logging.info(f"Scraping NCU Club: {sites['ncu_club']['url']}")
            all_items.extend(scrape_ncu_club(config))
        except Exception as e:
            msg = f"Error building NCU Club scraper: {str(e)}"
            logging.error(msg)
            error_log.append(msg)
            
    if sites.get('ncu_finance', {}).get('enabled', False):
        try:
            logging.info(f"Scraping NCU Finance: {sites['ncu_finance']['url']}")
            all_items.extend(scrape_ncu_finance(config))
        except Exception as e:
            msg = f"Error building NCU Finance scraper: {str(e)}"
            logging.error(msg)
            error_log.append(msg)

    if sites.get('ncu_incu', {}).get('enabled', False):
        try:
            logging.info(f"Scraping NCU iNCU: {sites['ncu_incu']['url']}")
            all_items.extend(scrape_ncu_incu(config))
        except Exception as e:
            msg = f"Error building NCU iNCU scraper: {str(e)}"
            logging.error(msg)
            error_log.append(msg)
            
    if sites.get('ncu_career', {}).get('enabled', False):
        try:
            logging.info(f"Scraping NCU Career: {sites['ncu_career']['url']}")
            all_items.extend(scrape_ncu_career(config))
        except Exception as e:
            msg = f"Error building NCU Career scraper: {str(e)}"
            logging.error(msg)
            error_log.append(msg)

    if sites.get('google_site', {}).get('enabled', False):
        try:
            logging.info(f"Scraping Adaptive Learning: {sites['google_site']['url']}")
            all_items.extend(scrape_google_site(config))
        except Exception as e:
            msg = f"Error building Google Site scraper: {str(e)}"
            logging.error(msg)
            error_log.append(msg)

    # 3. Scrape KOCPC
    if config.get('kocpc', {}).get('enabled', False):
        try:
            logging.info(f"Scraping KOCPC: {config['kocpc']['url']}")
            from scrapers.kocpc import scrape_kocpc
            all_items.extend(scrape_kocpc(config['kocpc']['url']))
        except Exception as e:
            msg = f"Error building KOCPC scraper: {str(e)}"
            logging.error(msg)
            error_log.append(msg)

    # 3. Scrape Facebook Groups
    if sites.get('facebook', {}).get('enabled', False):
        try:
            from scrapers.facebook import scrape_facebook_page
            logging.info("Scraping Facebook Groups/Pages...")
            fb_items = scrape_facebook_page(config)
            all_items.extend(fb_items)
        except Exception as e:
            msg = f"Error scraping Facebook Pages: {str(e)}"
            logging.error(msg)
            error_log.append(msg)

    # 3.5 Personal Feed "Doom Scroll"
    if config['sites'].get('facebook', {}).get('feed_enabled', False):
        try:
            from scrapers.facebook import scrape_personal_feed
            logging.info("Starting Personal Feed Doom Scroll...")
            feed_items = scrape_personal_feed(config)
            all_items.extend(feed_items)
        except Exception as e:
            msg = f"Error scraping Facebook Feed: {str(e)}"
            logging.error(msg)
            error_log.append(msg)

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
    
    if not new_items and not error_log:
        logging.info("No new items found and no errors. Skipping email.")
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
    report_html = summarize_and_format(grouped_data, error_log)
    
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
        logging.info("Attempting to send Discord webhook...")
        send_discord_webhook(config, subject, report_html, error_log)

    # 7. Save History
    save_history(history)

if __name__ == "__main__":
    main()
