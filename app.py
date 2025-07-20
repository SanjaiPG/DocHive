import fitz  # PyMuPDF
import os
import json
import re
from collections import Counter, defaultdict

def extract_outline_from_pdf(file_path):
    doc = fitz.open(file_path)
    
    # First pass: collect all text with formatting information
    all_text_info = []
    font_sizes = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = ""
                font_size = 0
                is_bold = False
                bbox = line.get("bbox", [0, 0, 0, 0])
                
                for span in line["spans"]:
                    line_text += span["text"]
                    font_size = max(font_size, span["size"])
                    # Check if text is bold (flags & 2^4 = 16)
                    if span.get("flags", 0) & 16:
                        is_bold = True
                    font_sizes.append(span["size"])
                
                line_text = line_text.strip()
                if line_text and len(line_text) > 1:
                    all_text_info.append({
                        "text": line_text,
                        "font_size": round(font_size, 1),
                        "is_bold": is_bold,
                        "page": page_num + 1,
                        "bbox": bbox
                    })
    
    # Determine font size statistics
    font_counter = Counter([round(size, 1) for size in font_sizes])
    sorted_sizes = sorted(font_counter.keys(), reverse=True)
    
    # Get the most common font size (likely body text)
    most_common_size = font_counter.most_common(1)[0][0] if font_counter else 12.0
    
    # Define heading criteria
    def is_likely_heading(text_info):
        text = text_info["text"]
        font_size = text_info["font_size"]
        is_bold = text_info["is_bold"]
        
        # Skip very long texts (likely paragraphs)
        if len(text) > 100:
            return False
        
        # Skip texts with too many lowercase words (likely body text)
        words = text.split()
        if len(words) > 3:
            lowercase_ratio = sum(1 for word in words if word.islower() and len(word) > 2) / len(words)
            if lowercase_ratio > 0.6:
                return False
        
        # Heading indicators
        size_factor = font_size > most_common_size * 1.1  # Larger than body text
        bold_factor = is_bold
        format_factor = (
            text.isupper() or  # All caps
            text.istitle() or  # Title case
            bool(re.match(r'^[A-Z]', text)) or  # Starts with capital
            bool(re.match(r'^\d+\.', text)) or  # Numbered heading
            text.endswith(':')  # Ends with colon
        )
        
        # Skip common non-heading patterns
        if any(pattern in text.lower() for pattern in ['page', 'figure', 'table', '•', 'http', 'www']):
            return False
        
        # Must meet at least 2 criteria for heading
        criteria_met = sum([size_factor, bold_factor, format_factor])
        return criteria_met >= 2
    
    # Filter potential headings
    potential_headings = [info for info in all_text_info if is_likely_heading(info)]
    
    # Determine heading levels based on font size
    heading_sizes = list(set([h["font_size"] for h in potential_headings]))
    heading_sizes.sort(reverse=True)
    
    # Map font sizes to heading levels
    size_to_level = {}
    for i, size in enumerate(heading_sizes[:3]):  # Only H1, H2, H3
        if i == 0:
            size_to_level[size] = "H1"
        elif i == 1:
            size_to_level[size] = "H2"
        elif i == 2:
            size_to_level[size] = "H3"
    
    # Build outline
    outline = []
    for heading in potential_headings:
        level = size_to_level.get(heading["font_size"])
        if level:
            # Clean up heading text
            clean_text = heading["text"].strip()
            # Remove bullet points and numbering
            clean_text = re.sub(r'^[•\-\]\s', '', clean_text)
            clean_text = re.sub(r'^\d+\.\s*', '', clean_text)
            
            if clean_text:
                outline.append({
                    "level": level,
                    "text": clean_text,
                    "page": heading["page"]
                })
    
    # Remove duplicates while preserving order
    seen = set()
    unique_outline = []
    for item in outline:
        key = (item["level"], item["text"], item["page"])
        if key not in seen:
            seen.add(key)
            unique_outline.append(item)
    
    # Determine title (first H1 or largest heading)
    title = "Unknown Document"
    h1_headings = [item for item in unique_outline if item["level"] == "H1"]
    if h1_headings:
        title = h1_headings[0]["text"]
    elif unique_outline:
        title = unique_outline[0]["text"]
    
    doc.close()
    
    return {
        "title": title,
        "outline": unique_outline
    }

# Usage Example
if _name_ == "_main_":
    input_dir = "/content/input"  # Changed to match Docker requirements
    output_dir = "/content/output"  # Changed to match Docker requirements
    os.makedirs(output_dir, exist_ok=True)
    
    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(input_dir, file_name)
            output_path = os.path.join(output_dir, file_name.replace(".pdf", ".json"))
            
            try:
                result = extract_outline_from_pdf(file_path)
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                
                print(f"Processed: {file_name}")
            except Exception as e:
                print(f"Error processing {file_name}: {str(e)}")