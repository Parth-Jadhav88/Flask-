import os
import re
import fitz  # PyMuPDF
import spacy
from docx import Document
from flask import Flask, render_template, request

# Load NLP model once at the start
nlp = spacy.load("en_core_web_sm")

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'

# ------------------ Text Extractors ------------------

def extract_text_from_pdf(file_path):
    doc = fitz.open(file_path)
    text = ""
    for page in doc:
        text += page.get_text()
    doc.close()
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# ------------------ NLP Info Extractors ------------------

def extract_email(text):
    emails = re.findall(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text)
    return emails[0] if emails else "Not found"


def extract_phone(text):
    pattern = r'(\+91[\-\s]?)?[789]\d{9}\b'
    phones = re.findall(pattern, text)
    return phones[0] if phones else "Not found"

def extract_name(text):
    # Fallback using first few lines (common name position)
    lines = text.strip().split('\n')
    for line in lines:
        if len(line.strip().split()) >= 2 and len(line.strip()) < 50:
            return line.strip()
        break

    # Backup: spaCy-based detection
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            return ent.text
    return "Not found"

skills = ['python', 'java', 'html', 'css', 'sql', 'flask', 'opencv', 'ml']

def extract_skills(text):
    found = []
    for skill in skills:
        if skill.lower() in text.lower():
            found.append(skill)
    return list(set(found))

# ------------------ Routes ------------------

@app.route("/")
def home():
    return render_template("extrator.html")

@app.route("/submit", methods=["POST"])
def submit():
    file = request.files['resume']
    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        if filename.endswith('.pdf'):
            extracted_text = extract_text_from_pdf(file_path)
        elif filename.endswith('.docx'):
            extracted_text = extract_text_from_docx(file_path)
        else:
            return "Unsupported file format"

        # NLP Extraction
        name = extract_name(extracted_text)
        email = extract_email(extracted_text)
        phone = extract_phone(extracted_text)
        matched_skills = extract_skills(extracted_text)

        return f"""
<h2>Extracted Resume Details:</h2>
<b>Name:</b> {name}<br>
<b>Email:</b> {email}<br>
<b>Phone:</b> {phone}<br>
<b>Skills:</b> {', '.join(matched_skills)}<br>
<hr>
<h3>Full Extracted Text:</h3><pre>{extracted_text}</pre>
"""

    return "No file uploaded"

if __name__ == "__main__":
    app.run(debug=True)