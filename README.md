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
