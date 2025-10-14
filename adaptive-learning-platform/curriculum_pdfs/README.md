# Curriculum PDFs Storage

This folder contains the Sierra Leone curriculum PDFs for the Adaptive Learning Platform.

## Folder Structure

```
curriculum_pdfs/
├── grade_10_12/
│   ├── mathematics/     # Grade 10-12 Mathematics curriculum PDFs
│   ├── english/         # Grade 10-12 English curriculum PDFs
│   └── science/         # Grade 10-12 Science curriculum PDFs
```

## How to Add PDFs

1. **Place your PDFs in the appropriate subject folder:**
   - Mathematics PDFs → `grade_10_12/mathematics/`
   - English PDFs → `grade_10_12/english/`
   - Science PDFs → `grade_10_12/science/`

2. **PDF Naming Convention:**
   - Use descriptive names like: `grade_10_algebra.pdf`, `grade_11_grammar.pdf`
   - Include grade level and topic in the filename
   - Use underscores instead of spaces

3. **Run the PDF processing script:**
   ```bash
   cd backend
   python scripts/process_curriculum_pdfs.py
   ```

## Supported PDF Formats

- Standard PDF files (.pdf)
- Text-based PDFs work best (not scanned images)
- PDFs should contain readable text content

## Processing

The system will:
- Extract text content from PDFs
- Create embeddings for search functionality
- Store content in ChromaDB for AI-powered lesson generation
- Index by subject, grade, and topic for easy retrieval

## Example Files

```
grade_10_12/mathematics/
├── grade_10_algebra.pdf
├── grade_10_geometry.pdf
├── grade_11_calculus.pdf
├── grade_11_statistics.pdf
├── grade_12_advanced_math.pdf
└── grade_12_mathematical_methods.pdf

grade_10_12/english/
├── grade_10_literature.pdf
├── grade_10_composition.pdf
├── grade_11_advanced_writing.pdf
├── grade_11_literary_analysis.pdf
├── grade_12_creative_writing.pdf
└── grade_12_critical_thinking.pdf

grade_10_12/science/
├── grade_10_physics.pdf
├── grade_10_chemistry.pdf
├── grade_10_biology.pdf
├── grade_11_advanced_physics.pdf
├── grade_11_organic_chemistry.pdf
├── grade_11_human_biology.pdf
├── grade_12_quantum_physics.pdf
├── grade_12_biochemistry.pdf
└── grade_12_environmental_science.pdf
```

