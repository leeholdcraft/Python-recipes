from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from flask_bcrypt import Bcrypt
app= Flask(__name__)
app.secret_key = 'My super secret key'
bcrypt = Bcrypt(app)

import re
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9.+_-]+@[a-zA-Z0-9._-]+\.[a-zA-Z]+$')

@app.route('/')
def begin():
    return render_template("login.html")

@app.route('/adduser', methods=['POST'])
def register():
    is_valid = True
    if len(request.form['first_name']) < 2:
        is_valid = False
        flash("Please enter a first name")
    if len(request.form['last_name']) < 2:
        is_valid = False
        flash("Please enter a last name")
    if not EMAIL_REGEX.match(request.form['email']):
        is_valid= False
        flash("Invalid email address!")
    if len(request.form['password']) < 8:
        is_valid = False
        flash("Please enter a password with at least 8 characters")
    if request.form['password'] != request.form['confirm']:
        is_valid = False
        flash("Passwords must match")
    mysql = connectToMySQL("recipes")
    query = "SELECT * FROM users WHERE email= %(email)s;"
    data = {
        "email": request.form["email"],
        }
    result = mysql.query_db(query, data)
    if len(result) > 0:
        is_valid=False
        flash("Email already used")
    if not is_valid:
        return redirect("/")

    else:
        pw_hash = bcrypt.generate_password_hash(request.form['password'])
        mysql = connectToMySQL("recipes")
        query = "INSERT INTO users (first_name, last_name, email, password) VALUES (%(first_name)s, %(last_name)s, %(email)s, %(password_hash)s);"
        data = {
            "first_name": request.form['first_name'],
            "last_name": request.form['last_name'],
            "email": request.form["email"],
            "password_hash": pw_hash ,
            }
        newuser = mysql.query_db(query, data)
        session['username'] = newuser
        print (newuser)
        flash("You have successfully registered!")
        return redirect('/welcome')

@app.route('/login', methods=['POST'])
def login():
    mysql = connectToMySQL("recipes")
    query = "SELECT * FROM users WHERE email = %(email)s;"
    data = { "email" : request.form["email"] }
    result = mysql.query_db(query, data)
    if len(result) > 0:
        if bcrypt.check_password_hash(result[0]['password'], request.form['password']):
            session['userid'] = result[0]['id']
            session['username'] = result[0]['first_name']
            return redirect('/welcome')
        else:
            flash('Invalid email/password combination')
    else:
        flash("Email not in database")
        return redirect("/welcome")

@app.route('/welcome')
def success():
    user_id = session['userid']
    mysql = connectToMySQL("recipes")
    user = mysql.query_db('SELECT * FROM users')

    mysql = connectToMySQL("recipes")
    query = "SELECT * FROM content JOIN users on users.id= users_id WHERE users_id = %(id)s;" 
    data = {
            "id": session['userid']
        }
    recipes= mysql.query_db(query, data)
    return render_template("welcome.html", user=user[0], content=recipes)

@app.route("/show/<recipe_id>")
def show(recipe_id):
    mysql = connectToMySQL("recipes")
    query = "SELECT * FROM content JOIN users on users.id= users_id WHERE content.id= %(recipe_id)s;"
    data = {
        "recipe_id": recipe_id
    }
    recipe=mysql.query_db(query,data)
    print(recipe)
    return render_template("view.html", recipe=recipe)

@app.route("/edit/<recipe_id>")
def edit_user(recipe_id):
    mysql = connectToMySQL("recipes")
    query = "SELECT * FROM content WHERE id = (%(content_id)s);"
    data = {
        "content_id": recipe_id
    }
    recipe=mysql.query_db(query,data)
    print(recipe)
    return render_template("edit.html", recipe=recipe)

@app.route("/updated/<recipe_id>", methods=['POST'])
def edit(recipe_id):
    mysql= connectToMySQL("recipes")
    query= ("UPDATE content SET name = %(name)s, time = %(time)s, instruction = %(inst)s, description = %(desc)s WHERE id= %(recipe_id)s;")
    data = {
        "name": request.form["name"],
        "time": request.form["time"],
        "inst" : request.form["instruction"],
        "desc" : request.form["description"],
        "recipe_id": recipe_id
    }
    update=mysql.query_db(query,data)
    print(update)
    return redirect('/welcome')

@app.route('/delete/<recipe_id>')
def delete(recipe_id):
    mysql = connectToMySQL("recipes")
    query="DELETE FROM content WHERE id = %(recipe_id)s"
    data={
        "recipe_id": recipe_id
    }
    mysql.query_db(query, data)
    return redirect('/welcome')

@app.route('/addnew')
def write_new():
    return render_template('new.html')

@app.route("/new_recipe", methods=['POST'])
def add_new():
    mysql = connectToMySQL("recipes")
    query="INSERT INTO content (name, instruction, description, time, users_id) VALUES (%(name)s, %(inst)s, %(desc)s, %(time)s, %(user)s);"
    data={
        "name": request.form['name'],
        "inst": request.form['instruction'],
        "desc": request.form['description'],
        "time": request.form['time'],
        "user": session['userid']
    }
    mysql.query_db(query, data)
    return redirect('/welcome')

@app.route('/logout', methods=["POST"])
def logout():
    session.clear()
    return render_template("logout.html")


if __name__== "__main__":
    app.run(debug= True)