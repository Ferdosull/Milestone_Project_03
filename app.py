import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env


app = Flask(__name__)


app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")


mongo = PyMongo(app)

# My Routes


@app.route("/")
@app.route("/get_recipes")
def get_recipes():
    """
    function to get and display all recipes from db
    grabs the recipes from mongoDB
    displays all recipes on landing page
    """
    recipes = mongo.db.recipes.find()
    return render_template("recipes.html", recipes=recipes)


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    function to log the user in
    check if user exists in db
    check password linked to user
    if not correct show error
    if user does not exist, redirect
    """
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            if check_password_hash(
                    existing_user["password"], request.form.get("password")):
                session["user"] = request.form.get("username").lower()
                flash("Welcome, {}".format(
                    request.form.get("username")))
                return redirect(url_for("profile", username=session["user"]))
            else:
                flash("Incorrect Username or Password")
                return redirect(url_for("login"))

        else:
            flash("Incorrect Username or Password")
            return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/profile/<username>", methods=["GET", "POST"])
def profile(username):
    """
    function to display the users profile
    grab the session users name from db
    find all recipes associated with user
    display these recipes in the profile page
    """
    username = mongo.db.users.find_one(
        {"username": session["user"]})["username"]
    recipes = mongo.db.recipes.find()

    if session["user"]:
        return render_template(
            "profile.html", username=username, recipes=recipes)

    return redirect(url_for("login"))


@app.route("/logout")
def logout():
    """
    function to log the user out
    remove user from session cookie
    display a flash message to user
    redirect the user to the log in page
    """
    flash("You have been logged out")
    session.pop("user")
    return redirect(url_for("login"))


@app.route("/signup", methods=["GET", "POST"])
def signup():
    """
    function to sign up with the SS&J community
    check if username already exists in db
    if the username exists send a flash message
    if the user doesnt exist creat object "signup"
    insert this new user and password to the users collection
    put the new user into 'session' cookie
    """
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username").lower()})

        if existing_user:
            flash("Username already exists")
            return redirect(url_for("signup"))

        signup = {
            "username": request.form.get("username").lower(),
            "password": generate_password_hash(request.form.get(
                "confirm_password"))
        }
        mongo.db.users.insert_one(signup)

        session["user"] = request.form.get("username").lower()
        flash("Registration Successful!")
        return redirect(url_for("profile", username=session["user"]))

    return render_template("signup.html")


@app.route("/display_recipe/<task_id>", methods=["GET", "POST"])
def display_recipe(task_id):
    """
    function to display a single recipe
    grab the recipe selected task_id
    use the task_id to pull the recipe data from db
    pull the "steps" object out individually
    display the selected recipe and steps
    """
    task = mongo.db.recipes.find_one({"_id": ObjectId(task_id)})
    steps = task.get("steps")

    return render_template(
        "display_recipe.html",
        task=task, steps_dict=steps)


@app.route("/new_recipe", methods=["GET", "POST"])
def new_recipe():
    """
    function to create a new recipe
    creating two objects and updating with form contents
    steps_dict_new_recipe is an object containing steps
    task is an object containing the rest of the submission
    steps_dict_new_recipe then becomes an item in the task object
    the task object is then submitted to the db as a new recipe
    """
    if request.method == "POST":
        steps_dict_new_recipe = {}
        for x in range(0, 10):
            if request.form.get("step" + str(x + 1)) != "":
                steps_dict_new_recipe.update(
                    {"step" + str(x + 1): request.form.get(
                        "step" + str(x + 1))})
            else:
                steps_dict_new_recipe.update(
                    {"step" + str(x + 1): ""})
        task = {
            "main_component_type": request.form.get("select1"),
            "drink_name": request.form.get("drink_name"),
            "ingredients": request.form.get("ingredients-input"),
            "allergen_warning": request.form.get("select"),
            "image_url": request.form.get("image-url"),
            "recommends": 0,
            "preparation_time": request.form.get("select3"),
            "difficulty_level": request.form.get("select2"),
            "created_by": session["user"],
            "user_likes": (""),
            "steps": steps_dict_new_recipe
        }
        mongo.db.recipes.insert_one(task)
        flash("Your New Recipe Was Added")
        return redirect(url_for("new_recipe"))

    return render_template("new_recipe.html")


@app.route("/edit_recipe/<task_id>", methods=["GET", "POST"])
def edit_recipe(task_id):
    """
    function to edit existing recipes
    creating two objects and updating with form contents
    steps_dict_edit is an object containing steps
    submit is an object containing the rest of the submission
    steps_dict_edit then becomes an item in the submit object
    the submit object is then submitted to the db as a new recipe
    """
    if request.method == "POST":
        likes = mongo.db.recipes.find_one({"_id": ObjectId(task_id)})
        steps_dict_edit = {}
        for x in range(0, 10):
            if request.form.get("step" + str(x + 1)) != "":
                steps_dict_edit.update(
                    {"step" + str(x + 1): request.form.get(
                        "step" + str(x + 1))})
            else:
                steps_dict_edit.update(
                    {"step" + str(x + 1): ""})
        submit = {
            "main_component_type": request.form.get("select1"),
            "drink_name": request.form.get("drink_name"),
            "ingredients": request.form.get("ingredients-input"),
            "allergen_warning": request.form.get("select"),
            "image_url": request.form.get("image-url"),
            "recommends": int(likes.get("recommends")),
            "preparation_time": request.form.get("select3"),
            "difficulty_level": request.form.get("select2"),
            "created_by": likes.get("created_by"),
            "user_likes": likes.get("user_likes"),
            "steps": steps_dict_edit
        }
        mongo.db.recipes.update({"_id": ObjectId(task_id)}, submit)
        flash("Recipe Successfully Updated")

    task = mongo.db.recipes.find_one({"_id": ObjectId(task_id)})
    edit_steps = task.get("steps")
    return render_template(
        "edit_recipe.html", task=task, edit_steps=edit_steps)


@app.route("/delete_recipe/<task_id>")
def delete_recipe(task_id):
    """
    function to delete a submitted recipe
    the recipe for deletion is selected based the task_id
    a flash message is returned to the user
    the user is redirected back to the profile page
    """
    mongo.db.recipes.remove({"_id": ObjectId(task_id)})
    flash("Recipe Successfully Deleted")
    return redirect(url_for("profile", username=session["user"]))


@app.route("/search", methods=["GET", "POST"])
def search():
    """
    function to search the preset indexes
    indexes chosen were, main_component_type
    drink_name and ingredients
    query is sent to db and all recipes
    matching the request are displayed
    """
    query = request.form.get("query")
    recipes = list(mongo.db.recipes.find({"$text": {"$search": query}}))
    return render_template("recipes.html", recipes=recipes)


@app.route("/update_likes/<task_id>", methods=["GET", "POST"])
def update_likes(task_id):
    """
    function to update the likes on a recipe
    the specific recipe is grabbed from the db using task_id
    the recommends value is extracted and incremented by 1
    the user likes value is extracted and the session user
    name is added to this var "user_likes" if not already present
    the new object "submit" is created with these new vars
    the db is then updated with new recommends and user_likes values
    """
    likes = mongo.db.recipes.find_one({"_id": ObjectId(task_id)})
    search_user = likes.get("user_likes")
    if session["user"] not in search_user:
        like = likes.get("recommends")
        new_val = int(like) + 1
        user_likes = likes.get("user_likes")
        user_likes = (user_likes + session["user"] + ", ")
        submit = {
            "main_component_type": likes.get("main_component_type"),
            "drink_name": likes.get("drink_name"),
            "ingredients": likes.get("ingredients"),
            "allergen_warning": likes.get("allergen_warning"),
            "image_url": likes.get("image_url"),
            "recommends": new_val,
            "preparation_time": likes.get("preparation_time"),
            "difficulty_level": likes.get("difficulty_level"),
            "created_by": likes.get("created_by"),
            "user_likes": user_likes,
            "steps": likes.get("steps")
        }
        mongo.db.recipes.update({"_id": ObjectId(task_id)}, submit)
        task = mongo.db.recipes.find_one({"_id": ObjectId(task_id)})
        steps_dict_replace = task.get("steps")
        return render_template(
            "display_recipe.html", task=task,
            steps_dict=steps_dict_replace)

    task = mongo.db.recipes.find_one({"_id": ObjectId(task_id)})
    steps_dict_replace = task.get("steps")
    return render_template(
        "display_recipe.html", task=task,
        steps_dict=steps_dict_replace)


if __name__ == "__main__":
    """
    Throughout the project creation
    debug has remained "True"
    before final push debug has
    been changed to "False"
    """
    app.run(host=os.environ.get("IP"),
            port=int(os.environ.get("PORT")),
            debug=False)
