
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
    1. **Strictly Filter**: Identify and **IGNORE** items that are:
       - **User Questions**: Asking for help, debugging advice (e.g. "Help me", "Why is this error?").
       - **Personal Show-off/Builds**: Personal computer builds, "Look at my new hardware", unboxing photos without technical review, vanity specs.
       - **Personal Life/Diaries (CRITICAL)**: "I retired", "Moved to new city", "Taking care of parents", "My thoughts on life", "Dinner photos", "Travel logs". **UNLESS** it is a major industry figure announcing a strategic career move (e.g. CEO of TSMC).
       - **Vague/Clickbait**: "You won't believe this", "Download this tool" (without context).

    2. **Synthesize**: Write a **Comprehensive Narrative Briefing** (in Traditional Chinese 繁體中文).
       - **Style**: **News Anchor / Magazine Style**. Write a smooth, engaging, and detailed article.
       - **Detail**: **MAXIMUM DETAIL**. Do not be brief. Expand on the "Who, What, Where, When, Why, and Impact" in a cohesive story.
       - **Structure**:
         - Write **ONE cohesive paragraph** (or two if needed) that weaves the items together.
         - **DO NOT** use bullet points or category headers (like 【🔥 Top Stories】). Write it like a seamless news report.
         - **Example**: "OpenAI 近日再次震撼業界，發布了其最新的文字生成影片模型Sora... 這項發展標誌著..."
       
    3. **Tone & Style**:
       - **Persona**: You are a **Smart Executive Assistant** (智慧型行政助理) reporting to your Boss.
       - **Tone**: Professional, Insightful, and Fluent.
       - **Citations (MANDATORY)**: Every news point MUST specify its source item title in brackets.
       
       - **CRITICAL**: Output format MUST be:
         
         報告老闆，(Start your narrative here...)

         ## Filtered Log

       - **IMPORTANT**: Do NOT add any other headers like "## Briefing" or "## Summary". Just the Narrative Paragraph and then the Filtered Log.
         
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
            # Use 'gemini-2.5-flash'
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = model.generate_content(prompt)
            result = response.text.strip()

        elif provider == 'groq':
            from groq import Groq
            client = Groq(api_key=api_key)
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a professional news editor. Output brief, structured Traditional Chinese."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000,
            )
            result = completion.choices[0].message.content.strip()
            
        else:
            return None
            
        return result
            
    except Exception as e:
        logging.error(f"AI Group Summarization failed: {e}")
        return None
