import keyword
import os
import re
import fitz  
from pydantic import validate_email
import spacy
from docx import Document
from flask import Flask, render_template, request
from db import get_db_connection
from flask import session

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
    return text # in each case this text variable is very important !!!

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

# ------------------ NLP / spacy Info Extractors ------------------

def extract_email(text):
    emails = re.findall(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', text) #needs clarifications !!! 
    return emails[0] if emails else "Not found"

 # extract_phone function 👇🏻 need to clarify !!!!!!   copyed from GPT !!-----------------------------------------------


import re
import unicodedata

def extract_phone(text):
    # Step 1: Normalize the text to remove strange unicode chars
    text = unicodedata.normalize("NFKD", text)

    # Step 2: Replace all types of whitespace (tab, newline, multiple spaces) with single space
    text = re.sub(r'\s+', '', text)

    # Step 3: Extract all digit sequences of 10 or more digits
    potential_numbers = re.findall(r'\+91[6-9]\d{9}|[6-9]\d{9}', text)

    # Step 4: Remove duplicates and return first match
    return list(set(potential_numbers))[0] if potential_numbers else "Not found"


#-------------------------------------------------------------------------------------------


def extract_name(text):
    # Fallback using first few lines (common name position)
    lines = text.strip().split('\n') # strip() absically rempves the extra spaces from the start and end of resume 
    # and split('\n') is used for split the line in the new line   like after [ . ]
    for line in lines: #starts looping from each line to line 
        if len(line.strip().split()) >= 2 and len(line.strip()) < 50: 
            # this thing works like line should be more than 2+ words and less than 50 characters !!
            return line.strip()
        break

    # Backup: spaCy-based detection
    doc = nlp(text)  # in this case this is running through spacy     like nlp(text ) this model reads test and try to detect the entities 

    for ent in doc.ents: #this is the loop for each n every entity which spacy founds 
        if ent.label_ == "PERSON": #if it detects the entity == PERSON in Spacy entities 
            return ent.text #it returns that entity 
    return "Not found" # else not found 

skills = ['python', 'java', 'html', 'css', 'sql', 'flask', 'opencv', 'ml']
# list for skills and can be modify as per need this is as per my resume for X


def extract_skills(text): 
    found = []# Empty list to store matched skills
    for skill in skills: # loop for the the skills to match in the skills string array 
        if skill.lower() in text.lower(): # Case-insensitive match between skill and resume text
            found.append(skill) # Add matched skill to the found list 
    return list(set(found)) # Remove duplicates and return final list of matched skills

education_keywords = [
    "ssc", "hsc", "10th", "12th", "diploma", "b.e", "btech", "b.tech", "mtech",
    "education", "degree", "university", "institute", "college", "school"
]


experience_keywords = [
    "intern", "internship", "worked", "experience", "project", "developed",
    "engineer", "role", "position", "responsibilities"
]


def extract_educational(text): 
    text = text.lower() # removing the problem of Capatilizations of alphabets !
    lines = text.split('\n')   # Split the resume text into lines for easier keyword scanning
    found = []  # List to store matched education-related lines 
    for line in lines: # going through each line by line of resume 
        if 10 < len(line) < 200:  # ✅ Only consider meaningful lines
          for edu_keyword in education_keywords:  # ✅ loop through education_keywords 
            if edu_keyword in line: #searching for educational keyword in by edu_keyword in line 
                found.append(line.strip()) # appending / adding the founded education keyword
                break
    return list(set(found)) 

def extract_experience(text):
    text = text.lower()
    lines = text.split('\n')
    found = []
    for line in lines:
        if 10 < len(line) < 200:  # Skip too short or overly long lines 
          for exp_keyword in experience_keywords:  # ✅ loop through experience_keywords
            if exp_keyword in line:
                found.append(line.strip())
                break
    return list(set(found))


#-------------------------- 8th jul ----------- 2025 !!!


import spacy
from spacy.matcher import Matcher

# Load English model
nlp = spacy.load("en_core_web_sm")

# List of common job titles – you can expand this
job_titles = [
    "Software Engineer", "Data Analyst", "Project Manager", "Team Lead",
    "Intern", "Backend Developer", "Frontend Developer", "AI Engineer",
    "Machine Learning Engineer", "Web Developer", "Data Scientist"
]

# Create matcher and add job title patterns
matcher = Matcher(nlp.vocab)
for title in job_titles:
    pattern = [{"LOWER": token.lower()} for token in title.split()]
    matcher.add("JOB_TITLE", [pattern])





def extract_designations(text):
    doc = nlp(text)
    matches = matcher(doc)
    designations = []

    for match_id, start, end in matches:
        span = doc[start:end]
        designations.append(span.text)

    return list(set(designations))  # Remove duplicates    



# ------------------ Routes ------------------

@app.route("/")
def home():
    return render_template("extractor.html")

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

        # ---------------- NLP + DB ----------------
        name = extract_name(extracted_text)
        email = extract_email(extracted_text)
        phone = extract_phone(extracted_text)
        matched_skills = extract_skills(extracted_text)
        experience = extract_experience(extracted_text)
        designations = extract_designations(extracted_text)
        full_experience = list(set(experience + designations))
        educational_qualification = extract_educational(extracted_text)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            sql = """
            INSERT INTO resumes 
            (candidate_email, filename, filepath, name, email, phone, skills, experience, education, extracted_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            candidate_email = session.get('email', 'not_logged_in')

            cursor.execute(sql, (
                candidate_email,
                filename,
                file_path,
                name,
                email,
                phone,
                ', '.join(matched_skills),
                ', '.join(full_experience),
                ', '.join(educational_qualification),
                extracted_text
            ))

            conn.commit()
            print("DB Commit Successful ✅")
            print("Rows inserted:", cursor.rowcount) 
            cursor.close()
            conn.close()

            # ✅ Return if all successful
            return f"""
            <h2>✅ Extracted Resume Details:</h2>
            <b>Name:</b> {name}<br>
            <b>Email:</b> {email}<br>
            <b>Phone:</b> {phone}<br>
            <b>Skills:</b> {', '.join(matched_skills)}<br>
            <b>Experience:</b> {', '.join(full_experience)}<br>
            <b>Education:</b> {', '.join(educational_qualification)}<br>
            <hr>
            <h3>📄 Full Extracted Text:</h3>
            <pre>{extracted_text}</pre>
            """
        
        except Exception as e:
            return f"<h3>❌ Database Error:</h3><pre>{str(e)}</pre>"
        


if __name__ == "__main__":
    app.run(debug=True)


# ih thhese functions which are below the looping structure is wrong like the keyword should be at the for loop for searching 
#it throught the the resume  

    # def extract_educational(text):
#     text=text.lower()
#     lines=text.split('\n')
#     found=[]
#     for line in lines :
#         if keyword in education_keywords:
#             found.append(line.strip())
#             break
#     return list(set(found))

# def extract_experience(text):
#     text=text.lower()
#     lines=text.split('\n')
#     found=[]
#     for line in lines:
#         if keyword in experience_keywords:
#             found.append(line.strip())
#             break
#     return list(set(found))

