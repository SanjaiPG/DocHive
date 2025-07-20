import fitz  # PyMuPDF
import os
import json
from collections import Counter, defaultdict

def extract_outline_from_pdf(file_path):
    doc = fitz.open(file_path)
    heading_candidates = []

    font_sizes = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]
        
        for block in blocks:
            if "lines" not in block:
                continue
            for line in block["lines"]:
                line_text = ""
                max_font_size = 0
                font_flags = []

                for span in line["spans"]:
                    line_text += span["text"].strip() + " "
                    font_sizes.append(span["size"])
                    max_font_size = max(max_font_size, span["size"])
                    font_flags.append(span.get("flags", 0))  # font style (bold/italic)

                line_text = line_text.strip()

                # Skip very short or empty lines
                if not line_text or len(line_text) < 3:
                    continue

                # Capture with position, font size, and style
                heading_candidates.append({
                    "text": line_text,
                    "size": max_font_size,
                    "flags": font_flags,
                    "page": page_num + 1
                })

    # Determine font size thresholds
    common_sizes = Counter([round(s, 1) for s in font_sizes]).most_common()
    sorted_sizes = sorted(set([size for size, _ in common_sizes]), reverse=True)

    size_to_level = {}
    if len(sorted_sizes) > 0:
        size_to_level[sorted_sizes[0]] = "H1"
    if len(sorted_sizes) > 1:
        size_to_level[sorted_sizes[1]] = "H2"
    if len(sorted_sizes) > 2:
        size_to_level[sorted_sizes[2]] = "H3"

    outline = []
    for item in heading_candidates:
        size = round(item["size"], 1)
        level = size_to_level.get(size)
        if level:
            outline.append({
                "level": level,
                "text": item["text"],
                "page": item["page"]
            })

    # Title guess: first large heading (H1)
    title = next((x["text"] for x in outline if x["level"] == "H1"), "Unknown Title")

    return {
        "title": title,
        "outline": outline
    }

# Usage Example
if __name__ == "__main__":
    input_dir = "/content/input"
    output_dir = "/content/output"
    os.makedirs(output_dir, exist_ok=True)

    for file_name in os.listdir(input_dir):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(input_dir, file_name)
            output_path = os.path.join(output_dir, file_name.replace(".pdf", ".json"))
            
            result = extract_outline_from_pdf(file_path)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"Processed: {file_name}")
