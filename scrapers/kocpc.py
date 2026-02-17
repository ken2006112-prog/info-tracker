
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import logging

def scrape_kocpc(url):
    """
    Scrapes the latest articles from Computer King Ada (https://www.kocpc.com.tw/).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = []
        # Selector based on inspection: article.jeg_post
        articles = soup.select('article.jeg_post')
        
        for article in articles[:5]: # Top 5
            try:
                # Title & Link
                title_tag = article.select_one('h3.jeg_post_title a') 
                if not title_tag:
                    continue
                    
                title = title_tag.text.strip()
                link = title_tag['href']
                
                # Date (e.g., "2026 年 02 月 17 日")
                date_str = ""
                date_tag = article.select_one('div.jeg_meta_date')
                if date_tag:
                    raw_date = date_tag.text.strip()
                    # Clean up "2026 年 02 月 17 日" -> "2026-02-17"
                    try:
                        raw_date = raw_date.replace(' ', '')
                        dt = datetime.strptime(raw_date, '%Y年%m月%d日')
                        date_str = dt.strftime('%Y-%m-%d')
                    except ValueError:
                        date_str = raw_date # Keep raw if Parse fails
                
                # Description
                description = ""
                desc_tag = article.select_one('div.jeg_post_excerpt p')
                if desc_tag:
                    description = desc_tag.text.strip()

                items.append({
                    'source': 'Computer King Ada (電腦王阿達)',
                    'title': title,
                    'link': link,
                    'date': date_str,
                    'description': description
                })
                
            except Exception as e:
                logging.error(f"Error parsing KOCPC article: {e}")
                continue
                
        return items

    except Exception as e:
        logging.error(f"Error scraping KOCPC: {e}")
        return []
