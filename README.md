# Adobe_Hackathon_1A 

# Team - Ritzy

## Overview

This project provides a Python-based solution to extract the outline (headings and subheadings) from PDF documents. The solution identifies headings based on font size, boldness, position, and text formatting, then organizes the headings into a structured outline format. The extracted outlines are saved as JSON files for further use.

## Features

- **PDF Outline Extraction**: Extracts headings, subheadings, and other relevant text based on certain heuristics such as font size and boldness.
- **Title Detection**: Automatically identifies the document's title by analyzing the most prominent headings in the first few pages.
- **JSON Output**: The extracted outline is saved in a clean JSON format, suitable for use in other applications or workflows.
- **Multiple PDFs**: Batch processing support for multiple PDF files from a specified input directory.

## Libraries and Tools

The solution uses the following libraries:

- **PyMuPDF (fitz)**: A Python library for extracting text, font size, and layout information from PDF files.
  - [PyMuPDF Documentation](https://pymupdf.readthedocs.io/)
  
- **OS**: Provides a portable way of using operating system-dependent functionality like reading/writing files and directories.
  
- **JSON**: Used for serializing the extracted outlines into JSON format for easy storage and interchange.

- **RE (Regular Expressions)**: Used for pattern matching to clean up headings and detect certain formats (like numbered lists or bullet points).

- **Collections (Counter)**: Helps with determining the most common font size to assist in identifying headings.

## How It Works

### 1. **Extracting Text Information**

The script opens each page of the PDF and retrieves text blocks, extracting detailed information about the font size, style (bold), and position (bounding box) of the text.

### 2. **Identifying Headings**

Headings are identified using a set of rules based on:
- **Font Size**: Larger font sizes are more likely to be headings.
- **Boldness**: Bold text is commonly used for headings.
- **Text Formatting**: Text patterns like uppercase, title case, or bullet points are considered.
- **Position**: Headings are more likely to appear near the top-left of the page.

The script applies these heuristics to filter potential headings from the document's text.

### 3. **Constructing the Outline**

Once potential headings are identified, the outline is structured hierarchically:
- The most prominent heading on a page is classified as a `H1`.
- Subheadings with slightly smaller font sizes are classified as `H2`, and so on.
- The script also attempts to merge headings that are close to each other vertically (on the same page) into a single heading.

### 4. **Title Detection**

The title of the document is determined by analyzing the largest headings on the first few pages. The most prominent group of headings near the top of the first page is chosen as the document title.

### 5. **Output**

The final outline, along with the document title, is saved in a structured JSON format.

## Input and Output

### Input

- **Directory**: `/app/input/`
  - The script expects PDF files placed in the input directory.
  - Only PDF files (`*.pdf`) are processed.

### Output

- **Directory**: `/app/output/`
  - The script generates a `.json` file for each PDF, containing the extracted outline and title.
  - Each JSON file is named after the input PDF file, with the extension `.json`.

### Example JSON Output

```json
{
  "title": "Document Title",
  "outline": [
    {
      "level": "H1",
      "text": "Introduction",
      "page": 0
    },
    {
      "level": "H2",
      "text": "Background",
      "page": 1
    },
    {
      "level": "H2",
      "text": "Methodology",
      "page": 2
    },
    {
      "level": "H3",
      "text": "Data Collection",
      "page": 2
    }
  ]
}
