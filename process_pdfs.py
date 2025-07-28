import fitz
import os
import json
import re
from collections import Counter

def extract_outline_from_pdf(file_path):
    doc = fitz.open(file_path)
    all_text_info = []
    font_sizes = []

    for page_num, page in enumerate(doc, start=0):
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
        return {"title": "", "outline": []}

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

        size_factor = font_size > most_common_size * 1.05
        bold_factor = is_bold
        format_factor = (
            text.isupper() or
            text.istitle() or
            bool(re.match(r'^[A-Z]', text)) or
            bool(re.match(r'^\d+[\.\)]', text)) or
            text.endswith(':')
        )
        left_margin_factor = left_x < 100

        if is_bold and font_size == most_common_size:
            return False

        lower_text = text.lower()
        if any(term in lower_text for term in ['page', 'figure', 'table', '•', 'http', 'www']):
            return False

        score = sum([size_factor, bold_factor, format_factor, left_margin_factor])
        return score >= 3

    potential_headings = [info for info in all_text_info if is_likely_heading(info)]
    heading_sizes = sorted({h["font_size"] for h in potential_headings}, reverse=True)

    size_to_level = {}
    if heading_sizes:
        for idx, size in enumerate(heading_sizes[:3]):
            size_to_level[size] = f"H{idx}"

    outline = []
    for heading in potential_headings:
        level = size_to_level.get(heading["font_size"])
        if not level:
            continue

        text = heading["text"]
        text = re.sub(r'^[•\-\]\s]*', '', text)
        text = re.sub(r'^\d+[\.\)]\s*', '', text)
        text = text.strip()

        if not text:
            continue

        if outline:
            last = outline[-1]
            if (last["page"] == heading["page"] and
                last["level"] == level and
                abs(heading["bbox"][1] - last.get("bbox", [0, 0, 0, 0])[1]) < 30):
                last["text"] += " " + text
                continue

        outline.append({
            "level": level,
            "text": text,
            "page": heading["page"],
            "bbox": heading["bbox"]
        })

    largest_size = heading_sizes[0] if heading_sizes else None
    largest_headings = [
        h for h in potential_headings
        if h["font_size"] == largest_size and h["page"] <= 2
    ]

    with fitz.open(file_path) as doc_check:
        page_heights = [doc_check[p].rect.height for p in range(len(doc_check))]

    largest_headings_top_half = [
        h for h in largest_headings if h["bbox"][1] < page_heights[h["page"]] / 2
    ]

    title = ""
    if largest_headings_top_half:
        groups = []
        largest_headings_top_half = sorted(largest_headings_top_half, key=lambda h: (h["page"], h["bbox"][1]))
        current_group = [largest_headings_top_half[0]]

        for curr in largest_headings_top_half[1:]:
            last = current_group[-1]
            same_page = curr["page"] == last["page"]
            same_bold = curr["is_bold"] == last["is_bold"]
            same_size = abs(curr["font_size"] - last["font_size"]) < 0.1
            close_vertically = abs(curr["bbox"][1] - last["bbox"][3]) < 30

            if same_page and same_bold and same_size and close_vertically:
                current_group.append(curr)
            else:
                groups.append(current_group)
                current_group = [curr]
        groups.append(current_group)

        best_group = max(groups, key=len)
        title = " ".join(line["text"] for line in best_group).strip()

    seen = set()
    unique_outline = []
    for item in outline:
        if title and item["text"] in title:
            continue
        key = (item["level"], item["text"], item["page"])
        if key not in seen:
            seen.add(key)
            item.pop("bbox", None)
            unique_outline.append(item)

    return {"title": title, "outline": unique_outline}


def main():
    input_dir = "/app/input"
    output_dir = "/app/output"
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if not filename.lower().endswith(".pdf"):
            continue
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename.rsplit(".", 1)[0] + ".json")
        result = extract_outline_from_pdf(input_path)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
