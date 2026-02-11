import os

def is_tutor_group(name):
    keywords = ['家教', 'Tutor', '伴讀', '找老師', '找學生']
    return any(k in name for k in keywords)

def process_files():
    # 1. Process Groups
    groups_file = 'source_list_groups_raw.txt'
    clean_groups = []
    
    if os.path.exists(groups_file):
        with open(groups_file, 'r') as f:
            lines = f.readlines()
        
        current_name = None
        for line in lines:
            line = line.strip()
            if not line: continue
            
            # Heuristic: Valid names are usually the first line of a block
            # Blocks seem to be separated by "Public group", member counts, etc.
            if line in ['Public group', 'Private group'] or 'members' in line or 'Works at' in line:
                continue
            
            # If it looks like a name (not numbers, not status)
            if len(line) > 1 and not line[0].isdigit():
                # Check if it was the previous name's leftover or a new one?
                # The format is: Name \n Type \n Members...
                # So we take every valid-looking line that isn't metadata.
                
                if not is_tutor_group(line):
                    clean_groups.append(line)

    # 2. Process General Sources (Profiles/Pages)
    sources_file = 'source_list_raw.txt'
    clean_pages = []
    
    if os.path.exists(sources_file):
        with open(sources_file, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line: continue
            if 'Works at' in line or 'Taipei' in line or line in ['Public group']: 
                continue # Skip metadata lines
            
            clean_pages.append(line)

    # 3. Generate YAML
    with open('sources_to_fill.yaml', 'w') as f:
        f.write("# Please add the URL for the pages/groups you want to track.\n")
        f.write("# I have filtered out the 'Tutor' keyowrds as requested.\n\n")
        
        f.write("facebook_pages_and_groups:\n")
        
        f.write("  # --- Priority / Tech / Science ---\n")
        for name in clean_groups:
            f.write(f"  - name: \"{name}\"\n")
            f.write(f"    url: \"\" # <--- PASTE URL HERE\n")
            
        f.write("\n  # --- Other Potential Pages ---\n")
        for name in clean_pages:
             f.write(f"  - name: \"{name}\"\n")
             f.write(f"    url: \"\" # <--- PASTE URL HERE\n")

if __name__ == "__main__":
    process_files()
