import fitz  # PyMuPDF
import os
import json
import re
from collections import Counter

def extract_outline_from_pdf(file_path):
    """
    Extracts a structured outline from a PDF by detecting headings based on font size, boldness,
    and formatting cues.
    Returns a dict with document title and outline items.
    """
    doc = fitz.open(file_path)

    all_text_info = []
    font_sizes = []

    for page_num, page in enumerate(doc, start=1):
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = ""
                max_font_size = 0
                bold_char_count = 0
                total_char_count = 0
                bbox = line.get("bbox", [0, 0, 0, 0])

                for span in line["spans"]:
                    text = span["text"]
                    line_text += text
                    size = round(span["size"], 1)
                    if size > max_font_size:
                        max_font_size = size
                    total_char_count += len(text)
                    if span.get("flags", 0) & 16:
                        bold_char_count += len(text)
                    font_sizes.append(size)

                line_text = line_text.strip()
                if line_text and len(line_text) > 1:
                    is_bold = (bold_char_count / total_char_count) > 0.5 if total_char_count else False
                    all_text_info.append({
                        "text": line_text,
                        "font_size": max_font_size,
                        "is_bold": is_bold,
                        "page": page_num,
                        "bbox": bbox
                    })

    doc.close()

    if not font_sizes:
        # No text found fallback
        return {"title": "Unknown Document", "outline": []}

    # Most common font size assumed to be body text
    most_common_size = Counter(font_sizes).most_common(1)[0][0]

    def is_likely_heading(text_info):
        text = text_info["text"]
        font_size = text_info["font_size"]
        is_bold = text_info["is_bold"]
        left_x = text_info["bbox"][0]

        if len(text) > 100:
            return False

        words = text.split()
        if len(words) > 3:
            lowercase_ratio = sum(1 for w in words if w.islower() and len(w) > 2) / len(words)
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
        left_margin_factor = left_x < 100

        # Avoid marking bold text with body font size as heading
        if is_bold and font_size == most_common_size:
            return False

        # Exclude common unwanted patterns
        lower_text = text.lower()
        if any(term in lower_text for term in ['page', 'figure', 'table', '•', 'http', 'www']):
            return False

        score = sum([size_factor, bold_factor, format_factor, left_margin_factor])
        return score >= 3

    potential_headings = [info for info in all_text_info if is_likely_heading(info)]

    # Unique font sizes sorted descending, pick top 3 for heading levels
    heading_sizes = sorted({h["font_size"] for h in potential_headings}, reverse=True)[:3]
    size_to_level = {size: f"H{idx+1}" for idx, size in enumerate(heading_sizes)}

    outline = []
    for heading in potential_headings:
        level = size_to_level.get(heading["font_size"])
        if not level:
            continue

        text = heading["text"]
        # Clean heading text from bullets, numbering, etc.
        text = re.sub(r'^[•\-\]\s]*', '', text)
        text = re.sub(r'^\d+[\.\)]\s*', '', text)
        text = text.strip()

        if text:
            outline.append({
                "level": level,
                "text": text,
                "page": heading["page"]
            })

    # Remove duplicates preserving order
    seen = set()
    unique_outline = []
    for item in outline:
        key = (item["level"], item["text"], item["page"])
        if key not in seen:
            seen.add(key)
            unique_outline.append(item)

    # Determine title
    title = "Unknown Document"
    h1s = [item for item in unique_outline if item["level"] == "H1"]
    if h1s:
        title = h1s[0]["text"]
    elif unique_outline:
        title = unique_outline[0]["text"]

    # Remove the title heading from the outline if present
    unique_outline = [item for item in unique_outline if item["text"] != title]

    return {"title": title, "outline": unique_outline}


if __name__ == "__main__":
    input_dir = "/content/input"
    output_dir = "/content/output"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".pdf"):
            continue
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename.rsplit(".", 1)[0] + ".json")

        try:
            result = extract_outline_from_pdf(input_path)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Processed: {filename}")
        except Exception as e:
            print(f"Error processing {filename}: {e}")
