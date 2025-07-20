import fitz  # PyMuPDF
import os
import json
import re
import logging
from collections import Counter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# Set input/output directories
input_dir = "D:/Adobe Hackathon/app/input"
output_dir = "D:/Adobe Hackathon/app/output"

def extract_text_info(doc):
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
                    text = span["text"]
                    if text.strip() == "":
                        continue
                    size = round(span["size"], 1)
                    font_sizes.append(size)
                    font_size = max(font_size, size)
                    if span.get("flags", 0) & 16:
                        is_bold = True
                    line_text += text

                line_text = line_text.strip()
                if line_text and len(line_text) > 1:
                    all_text_info.append({
                        "text": line_text,
                        "font_size": round(font_size, 1),
                        "is_bold": is_bold,
                        "page": page_num + 1,
                        "bbox": bbox
                    })

    return all_text_info, font_sizes

def is_likely_heading(text_info, body_size):
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

    size_factor = font_size > body_size * 1.1
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

def extract_outline_from_pdf(file_path, max_levels=4):
    doc = fitz.open(file_path)

    all_text_info, font_sizes = extract_text_info(doc)
    body_size = Counter(font_sizes).most_common(1)[0][0] if font_sizes else 12.0

    potential_headings = [info for info in all_text_info if is_likely_heading(info, body_size)]
    heading_sizes = sorted(set([h["font_size"] for h in potential_headings]), reverse=True)

    size_to_level = {}
    for i, size in enumerate(heading_sizes[:max_levels]):
        size_to_level[size] = f"H{i+1}"

    outline = []
    for heading in potential_headings:
        level = size_to_level.get(heading["font_size"])
        if level:
            clean_text = re.sub(r'^[•\-\]\s]*', '', heading["text"])
            clean_text = re.sub(r'^\d+[\.\)]\s*', '', clean_text)
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()
            if clean_text:
                outline.append({
                    "level": level,
                    "text": clean_text,
                    "page": heading["page"]
                })

    # Remove duplicates
    seen = set()
    unique_outline = []
    for item in outline:
        key = (item["level"], item["text"], item["page"])
        if key not in seen:
            seen.add(key)
            unique_outline.append(item)

    # Title detection
    title = "Unknown Document"
    title_candidates = [info for info in all_text_info if info["font_size"] >= body_size * 1.5]
    if title_candidates:
        title = title_candidates[0]["text"].strip()
    elif unique_outline:
        title = unique_outline[0]["text"]

    # Remove first H1 if it matches the title
    if unique_outline:
        first = unique_outline[0]
        if first["level"] == "H1" and first["text"].strip().lower() == title.strip().lower():
            unique_outline = unique_outline[1:]

    doc.close()
    return {
        "title": title,
        "outline": unique_outline,
        "title_entry": {
            "text": title,
            "page": title_candidates[0]["page"] if title_candidates else None
        }
    }

def process_pdfs():
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(input_dir, file_name)
            output_json = os.path.join(output_dir, file_name.replace(".pdf", ".json"))

            try:
                result = extract_outline_from_pdf(file_path)
                with open(output_json, "w", encoding="utf-8") as f:
                    json.dump(result, f, indent=2, ensure_ascii=False)
                logging.info(f"Processed: {file_name}")
            except Exception as e:
                logging.error(f"Error processing {file_name}: {str(e)}")

if _name_ == "_main_":
    process_pdfs()
