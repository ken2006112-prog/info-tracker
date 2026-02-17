
import os
import logging
import openai
import google.generativeai as genai

def summarize_group(source_name, items, config):
    """
    Summarizes a list of items from a specific source into one comprehensive report.
    """
    if not items:
        return None

    ai_config = config.get('ai', {})
    if not ai_config.get('enabled', False):
        return None
        
    provider = ai_config.get('provider', 'openai').lower()
    api_key = os.environ.get('AI_API_KEY') 
    if not api_key:
        api_key = ai_config.get('api_key')
    if not api_key:
        return None

    # Prepare input text from items
    items_text = ""
    for i, item in enumerate(items, 1):
        items_text += f"Item {i}:\nTitle: {item.get('title')}\nDescription: {item.get('description', '')}\n\n"

    prompt = f"""
    You are a professional Personal Assistant briefing your boss.
    
    Source: {source_name}
    Received Data:
    {items_text}

    **Task**:
    1. **Filter**: Identify and **IGNORE** items that are:
       - **User Questions**: Asking for help, debugging advice (e.g. "Help me", "Why is this error?").
       - **Personal Show-off/Builds**: Personal computer builds, "Look at my new hardware", "New Year New PC", unboxing photos without deep technical review, or just sharing a spec list for vanity. (e.g. "My new 9850X3D build", "Rate my cables", "Jimmy Ng's build").

    2. **Synthesize**: Write a **single, comprehensive briefing** (in Traditional Chinese 繁體中文) that combines the remaining valid **Knowledge/News/Activities**.
       - **PRIORITY 1**: Any info related to **National Central University (NCU / 中央大學)** or specific school departments.
       - **PRIORITY 2**: **Workshops (工作坊), Activities (活動), Events (講座), Competitions (比賽)**.
       - **PRIORITY 3**: **General Tech/Science News, Industry Trends, or Useful Knowledge**. (Do not filter these out).
    
    3. **Tone & Style**:
       - **Persona**: You are reporting to your Boss.
       - **Tone**: Professional, concise, but direct. Start with "Boss," or "報告老闆，".
       - **Content**: Focus on the *implications* and *key facts*. "Here is what happened..."
       - **Citations (MANDATORY)**: Every news point MUST specify its source item title in brackets.
         - Good: "NVIDIA發布新模型 (Item: NVIDIA PersonaPlex)..."
         - Bad: "NVIDIA發布了新模型..."
       
       - **Format**:
         - **Section 1: The Briefing** (The main summary).
         - **Section 2: Filtered Log** (List items you ignored and WHY, so I can double check).
         
       - **CRITICAL**: Output format MUST be:
         
         ## Briefing
         (Your summary here...)

         ## Filtered Log
         - [Title]: [Reason for filtering, e.g. "User Question", "Show-off"]
         - [Title]: [Reason]

       - If ALL items are filtered out, still output the "Filtered Log" section, but put "Nothing significant to report" in Briefing.

    **Output**:
    """

    try:
        if provider == 'openai':
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o-mini", 
                messages=[
                    {"role": "system", "content": "You are a professional news editor."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800 
            )
            result = response.choices[0].message.content.strip()
            
        elif provider == 'gemini':
            genai.configure(api_key=api_key)
            # Use 'gemini-2.5-flash' as it appears in the user's model list
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            result = response.text.strip()
            
        else:
            return None
            
        return result
            
    except Exception as e:
        logging.error(f"AI Group Summarization failed: {e}")
        return None
