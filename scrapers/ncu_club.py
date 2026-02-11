#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def scrape_ncu_club(config):
    """
    Scrapes the NCU Club website for latest announcements.
    Returns a list of dictionaries with 'title', 'date', and 'link'.
    """
    url = config['sites']['ncu_club']['url']
    logging.info(f"Scraping NCU Club: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        announcements = []
        
        # Look for the general announcements section based on the HTML provided earlier
        # The structure seemed to be list items with dates and links.
        # We'll use a generic approach to find list items containing dates in standard formats.
        
        # Based on previous analysis: 
        # <li class="..."><span class="date">...</span><a href="...">...</a></li>
        # Let's try to be robust.
        
        # Calculate yesterday's date
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        # logging.info(f"Filtering for announcements from: {yesterday}") # Optional debug

        for item in soup.find_all('li'):
            text = item.get_text()
            # Simple date check
            if any(char.isdigit() for char in text) and '-' in text:
                 # Extract link and title
                link_tag = item.find('a')
                if link_tag:
                    title = link_tag.get_text(strip=True)
                    link = link_tag.get('href')
                    if not link.startswith('http'):
                        link = requests.compat.urljoin(url, link)
                    
                    # Extract date
                    date_str = "Unknown"
                    import re
                    match = re.search(r'\d{4}-\d{2}-\d{2}', text)
                    if match:
                        date_str = match.group(0)
                    
                    # STRICT FILTER: Only include if date matches yesterday
                    if date_str == yesterday:
                        announcements.append({
                            'source': 'NCU Club',
                            'title': title,
                            'date': date_str,
                            'link': link
                        })
        
        return announcements # Already filtered

    except Exception as e:
        logging.error(f"Error scraping NCU Club: {e}")
        return []

if __name__ == "__main__":
    # Test run
    config = {'sites': {'ncu_club': {'url': 'https://club.adm.ncu.edu.tw/'}}}
    results = scrape_ncu_club(config)
    print(f"Found {len(results)} posts from yesterday.")
    for r in results:
        print(r)
