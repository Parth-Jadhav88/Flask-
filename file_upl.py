

from flask import Flask, request, render_template, redirect, url_for
from werkzeug.utils import secure_filename
import os
app=Flask(__name__)

UPLOAD_FOLDER='uploads'  # this thinng is used to  store the files which were uploaded on UPOAD_FOLDER into uploads folder 
ALLOWED_EXTENSIONS={'pdf','doc','docx'}  # Only files with these extensions are allowed to be uploaded


app.config['UPLOAD_FOLDER']=UPLOAD_FOLDER  

def allowed_file(filename):  #this function basically checks the file uploaded by the user is allowed or not , this 
    #splites the the file from right means it checks the part of file after . eg .pdf, .docx , .doc 
    return '.'in filename and filename.rsplit('.',1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def upload_form():
    return render_template('uploads.html') #this is the 1st thing which user will see  uploads html page #interface to upload file 

@app.route('/', methods=['POST']) 
def upload_files():
    if 'file' not in request.files:  # needs clarificatins   
        return 'no file  part'  # needs clarificatins   
    
    file=request.files['file']  #the file uploaded by the user through the request.files would be saved in variable name file 

    if file.filename=='':    # .filename inbuilt property of the FileStorage object.
        return ' no file selected '
    if file and allowed_file(file.filename): # cheks if file is present / uploaded and is in the corrct format by allowed_file function
        filename=secure_filename(file.filename) # secure_filename removes the blank spaces and risky char. from the filename itself
        print('allowed files ✅')

        file.save(os.path.join(app.config['UPLOAD_FOLDER'],filename))
        
        return  f'file {filename } uploaded successfuly  ' 
    
    return 'Invalid file type . only pdf , foc and docx file types allowed '



if __name__ =='__main__':
    app.run(debug=True)


