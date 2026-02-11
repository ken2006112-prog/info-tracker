import yaml
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
        
    # 3. Summarize
    report_html = summarize_and_format(all_data)
    
    # 4. Send Notifications
    today = datetime.now().strftime('%Y-%m-%d')
    subject = f"Info Tracker Daily Report - {today}"
    
    # Send Email if enabled
    if config.get('email', {}).get('enabled', False):
        send_email(config, subject, report_html)
        
    # Send Discord if enabled
    if config.get('discord', {}).get('enabled', False):
         # We need to import the new function specifically or update the import logic. 
         # Since we import * or specific functions, let's update the import line first if needed.
         # Actually, better to just update the import at top of file, but for now let's assume `notifier` module has it.
         from notifier import send_discord_webhook
         send_discord_webhook(config, subject, report_html)

if __name__ == "__main__":
    main()
