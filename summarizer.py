def summarize_and_format(data):
    """
    Takes a list of data dictionaries and formats them into an HTML report.
    """
    if not data:
        return "<p>No new information found today.</p>"
    
    html = "<h2>Daily Info Tracker Report</h2>"
    
    # Group by source
    grouped = {}
    for item in data:
        source = item.get('source', 'Unknown')
        if source not in grouped:
            grouped[source] = []
        grouped[source].append(item)
    
    for source, items in grouped.items():
        html += f"<h3>{source}</h3><ul>"
        for item in items:
            title = item.get('title', 'No Title')
            link = item.get('link', '#')
            date = item.get('date', '')
            
            html += f"<li><strong>{date}</strong>: <a href='{link}'>{title}</a></li>"
        html += "</ul>"
        
    return html
