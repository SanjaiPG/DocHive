# DocHive 
## Problem Statement
When working with large PDF documents (research papers, reports, books, manuals), extracting the **table of contents (TOC)** or **document structure** is not always straightforward.  
- Many PDFs **lack a proper outline/TOC** embedded in their metadata.  
- Machine learning–based approaches exist, but they can be **slow, require training data, and demand heavy dependencies**.  
- A lightweight, fast, and **model-free solution** is often more practical.

This project provides a **heuristic-based PDF outline extractor** that analyzes font size, boldness, and text patterns to detect **titles, headings, and subheadings** from PDF files.  

## Features  
- **No machine learning model needed** – purely heuristic rules.  
- **Very fast** – processes a 50-page PDF in ~5 seconds.  
- Extracts **document title** and **outline hierarchy (H0, H1, H2)**.  
- Works even when the PDF has **no embedded outline/TOC**.  
- Uses **font size, boldness, indentation, and formatting clues** to detect headings.  
- Supports **batch processing** (process all PDFs in a folder).  
- Saves results as **structured JSON files**. 

## How It Works  
The extractor follows a **heuristic approach**:  
1. Reads all text spans from the PDF using [PyMuPDF (`fitz`)](https://pymupdf.readthedocs.io/).  
2. Collects **font sizes, bold flags, and bounding boxes**.  
3. Applies rules to detect **likely headings** based on:  
   - Larger-than-normal font size  
   - Bold text usage  
   - Title case / uppercase / numbering (e.g., `1. Introduction`)  
   - Left margin alignment  
4. Builds a **document title** from the largest, topmost headings.  
5. Constructs an **outline hierarchy (H0/H1/H2)**.  
6. Saves output as JSON (with `title` + `outline`).
   ```json
   {
      "title": "Document Title",
      "outline": [
       { "level": "H0", "text": "Introduction", "page": 1 },
       { "level": "H1", "text": "Background", "page": 2 },
       { "level": "H2", "text": "Previous Work", "page": 3 }
      ]
   }
   ```
## Project Structure
```
dochive/
├── app/
│   ├── input/           # Place your PDF files here
│   └── output/          # Extracted JSON outlines will be saved here
├── process_pdfs.py      # Main extraction script
└── README.md
```

## Installation
### Prerequisites
- Python 3.7 or higher
- pip package manager

### Install Dependencies
```bash
pip install PyMuPDF
```

## Processing
### To process PDFs
1. Place your PDF files in the input/ directory
2. Run the script:
```bash
python process_pdfs.py 
```
3. Check the output/ directory for JSON results

## How to Run with Docker
You can use Docker to containerize and run the PDF outline extractor easily.

1. Build the Docker Image
Run this command in the project root (where your Dockerfile and process_pdfs.py are):
```
docker build -t pdf-outline-extractor .
```
This builds a Docker image named pdf-outline-extractor using Python 3.10-slim with PyMuPDF installed.

2. Run the Container
Run the container, mounting your local input and output directories into the container:
```
docker run --rm \
  -v /full/path/to/input:/app/input \
  -v /full/path/to/output:/app/output \
  pdf-outline-extractor
```
- Replace /full/path/to/input and /full/path/to/output with your actual directories on your machine.
- Place your PDF files inside the input directory before running.
- The extracted JSON outline files will be saved inside the output directory.

For CMD:
```
docker run --rm -v C:\full\path\to\input:/app/input -v C:\full\path\to\output:/app/output pdf-outline-extractor
```
3. Verify Output -
   After running, check the output folder for JSON files corresponding to your processed PDFs.

## Info

This project, **DocHive**, was developed as part of the **Adobe Hackathon 1A – Connecting Dots** round.

**Successfully qualified for the final round** with this solution.

### Adobe Hackathon Constraints

This project complies with the official constraints defined for Adobe Hackathon Round 1A:

| Constraint Type  | Requirement                          |
|------------------|--------------------------------------|
| Execution Time | ≤ 10 seconds for a 50-page PDF       |
| Model Size     | ≤ 200 MB (if any used)               |
| Network        | No internet access allowed           |
| Runtime        | Must run on **CPU only (amd64)**      |
| System Config  | Tested on 8 CPUs, 16 GB RAM setup     |
