import fitz  # PyMuPDF
import os
import json
import re
from collections import Counter

def extract_outline_from_pdf(file_path):
    doc = fitz.open(file_path)

    all_text_info = []
    font_sizes = []

    # Extract text from each page with formatting info
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
                    if span.get("flags", 0) & 16:  # bold flag
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

    # Get most common font size (assumed body text)
    font_counter = Counter([round(size, 1) for size in font_sizes])
    most_common_size = font_counter.most_common(1)[0][0] if font_counter else 12.0

    # Heading detection logic
    def is_likely_heading(text_info):
        text = text_info["text"]
        font_size = text_info["font_size"]
        is_bold = text_info["is_bold"]

        if len(text) > 100:
            return False

        words = text.split()
        if len(words) > 3:
            lowercase_ratio = sum(1 for word in words if word.islower() and len(word) > 2) / len(words)
            if lowercase_ratio > 0.6:
                return False

        size_factor = font_size > most_common_size * 1.1
        bold_factor = is_bold
        format_factor = (
            text.isupper() or
            text.istitle() or
            bool(re.match(r'^[A-Z]', text)) or
            bool(re.match(r'^\d+[\.\)]', text)) or
            text.endswith(':')
        )

        if any(term in text.lower() for term in ['page', 'figure', 'table', '•', 'http', 'www']):
            return False

        return sum([size_factor, bold_factor, format_factor]) >= 2

    potential_headings = [info for info in all_text_info if is_likely_heading(info)]

    # Identify unique font sizes in headings
    heading_sizes = sorted(set([h["font_size"] for h in potential_headings]), reverse=True)

    # Map top font sizes to heading levels
    size_to_level = {}
    for i, size in enumerate(heading_sizes[:3]):
        size_to_level[size] = f"H{i+1}"

    # Build outline
    outline = []
    for heading in potential_headings:
        level = size_to_level.get(heading["font_size"])
        if level:
            clean_text = heading["text"].strip()
            clean_text = re.sub(r'^[•\-\]\s]*', '', clean_text)
            clean_text = re.sub(r'^\d+[\.\)]\s*', '', clean_text)

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

    # Determine title
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

# Run on all PDFs in a folder
if __name__ == "__main__":
    input_dir = "/content/input"   # Input folder
    output_dir = "/content/output" # Output folder
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
