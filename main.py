import yaml
import json
import logging
import os
from datetime import datetime
from scrapers.ncu_club import scrape_ncu_club
from scrapers.facebook import scrape_facebook_page
from summarizer import summarize_and_format
from notifier import send_email

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def load_config(path='config.yaml'):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def main():
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    config = load_config(config_path)
    
    all_data = []
    
    # 1. Scrape NCU Club
    if config['sites']['ncu_club']['enabled']:
        ncu_data = scrape_ncu_club(config)
        all_data.extend(ncu_data)
        
    # 2. Scrape Facebook
    if config['sites']['facebook']['enabled']:
        # The facebook scraper expects a slightly different config structure in the loop
        # But we designed it to take the whole config object.
        fb_data = scrape_facebook_page(config)
        all_data.extend(fb_data)
        
    # 3. Scrape iNCU
    if config['sites'].get('ncu_incu', {}).get('enabled'):
        from scrapers.ncu_incu import scrape_ncu_incu
        all_data.extend(scrape_ncu_incu(config))

    # 4. Scrape NCU Career
    if config['sites'].get('ncu_career', {}).get('enabled'):
        from scrapers.ncu_career import scrape_ncu_career
        all_data.extend(scrape_ncu_career(config))

    # 5. Scrape Google Site
    if config['sites'].get('google_site', {}).get('enabled'):
        from scrapers.google_site import scrape_google_site
        all_data.extend(scrape_google_site(config))
        
    # --- HISTORY / MEMORY IMPLEMENTATION ---
    history_file = os.path.join(os.path.dirname(__file__), 'history.json')
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except Exception as e:
            logging.error(f"Failed to load history: {e}")

    # Helper to check if item is in history
    # We use URL as the unique identifier. 
    # If URL is missing or generic, we use Title + Date.
    history_ids = {item.get('url') for item in history if item.get('url')}
    
    def is_new(item):
        if item.get('url') in history_ids:
            return False
        # Fallback for items without unique URLs (rare but possible)
        return True

    # 4. Filter Data (Memory + Date)
    new_items = []
    
    # Date Filter: For sources that provide a proper date (YYYY-MM-DD), 
    # we can filter for "Yesterday" or "Today" if desired.
    # However, user also wants "Memory". Memory is safer. 
    # If we filter strictly by date, we might miss things if the scraper fails one day.
    # So we prioritize Memory (is_new). 
    
    # We can still sort them or highlight them, but let's stick to "New since last run".
    
    for item in all_data:
        if is_new(item):
            new_items.append(item)
            
    logging.info(f"Total items scraped: {len(all_data)}")
    logging.info(f"New items to report: {len(new_items)}")
    
    if not new_items:
        logging.info("No new items found. Skipping email.")
        return

    # 5. Summarize
    report_html = summarize_and_format(new_items)
    
    # 6. Send Notifications
    today = datetime.now().strftime('%Y-%m-%d')
    subject = f"Info Tracker Daily Report - {today} ({len(new_items)} new)"
    
    # Send Email if enabled
    if config.get('email', {}).get('enabled', False):
        send_email(config, subject, report_html)
        
    # Send Discord if enabled
    if config.get('discord', {}).get('enabled', False):
         from notifier import send_discord_webhook
         send_discord_webhook(config, subject, report_html)

    # 7. Update History
    # We append new items to history. 
    # To prevent history from growing infinitely, we can keep the last 1000 items.
    history.extend(new_items)
    
    # Keep last 1000
    if len(history) > 1000:
        history = history[-1000:]
        
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
