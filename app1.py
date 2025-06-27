from flask import Flask, Response, redirect, url_for, request, session,render_template

app = Flask(__name__)
app.secret_key = "supersecret"

@app.route('/', methods=["GET", "POST"]) # get is just used to  To display the login form. and the POST is used to To process the login form.
def login():
    if request.method == "POST":
        username = request.form.get("username")# request.form.get is used to extract the data which is entered by the used in html form 
        password = request.form.get("password")

        if username == "admin" and password == "1234":  # this is like the basic if condition it allows the user with admin and pass 1234 to login only 

            session["user"] = username # this stores the the username entered by user in session this is like an temp. storage 

            return redirect(url_for("welcome"))
        else:
            return "Invalid credentials"

    # Show the login form on GET request

    return '''
<h2>Login Page</h2>
<form method="POST">
    Username: <input type="text" name="username"><br>
    Password: <input type="password" name="password"><br>
    <input type="submit" value="Login">
</form>
    '''


@app.route("/welcome")
def welcome():
    if "user" in session:
        return f'''
<h2>Welcome {session["user"]} !!!</h2>
<a href="{url_for('logout')}">Logout</a>
        '''
    else:
        return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))
    

if __name__ == "__main__":
    app.run(debug=True)



