import pandas as pd
import datetime
import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user
from flask_login import logout_user, login_required
from forms import RegistrationForm, LoginForm, PostForm, PPForm

app = Flask(__name__)

app.config["SECRET_KEY"] = "enter-a-hard-to-guess-string"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(user_id)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(60), nullable=False)
    lname = db.Column(db.String(60), nullable=False)
    uname = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    profilepic = db.Column(db.String(100), default=None)
    posts = db.relationship("Posts", backref="op", lazy=True)

    def __repr__(self):
        return f"User(id: '{self.id}', fname: '{self.fname}', " +\
               f" lname: '{self.lname}', uname: '{self.uname}')" +\
               f" password: '{self.password}', email: '{self.email}')"


class Posts(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(140), nullable=False)
    length = db.Column(db.String(10), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False,
                             default=datetime.datetime.now)
    imgn = db.Column(db.String(100))
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    def __repr__(self):
        return f"Product(id: '{self.id}', conrent: '{self.content}', " +\
               f" length: '{self.length}', " +\
               f" date_created: '{self.date_created}', " +\
               f" imgn: '{self.imgn}', op: '{self.user_id}')"


@app.route("/")
def index():
    if current_user.is_authenticated:
        posts = get_posts()
        return render_template("index.html", posts_df=posts, User=User)
    else:
        return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = RegistrationForm()

    if form.validate_on_submit():
        registration_worked = register_user(form)
        if registration_worked:
            return redirect(url_for("login"))

    return render_template("register.html", form=form, User=User)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    form = LoginForm()

    if form.validate_on_submit():
        if is_login_successful(form):
            return redirect(url_for("index"))
        else:
            if User.query.filter_by(email=form.email.data).count() > 0:
                flash("Login unsuccessful, please check your credentials and try again")
            else:
                return redirect(url_for("register"))
    return render_template("login.html", form=form, User=User)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


def register_user(form_data):
    def email_already_taken(email):
        if User.query.filter_by(email=email).count() > 0:
            return True
        else:
            return False

    def uname_already_taken(uname):
        if User.query.filter_by(uname=uname).count() > 0:
            return True
        else:
            return False
    if email_already_taken(form_data.email.data):
        flash("That email is already taken!")
        return False
    if uname_already_taken(form_data.uname.data):
        flash("That username is already taken!")
        return False

    hashed_password = bcrypt.generate_password_hash(form_data.password.data)
    user = User(fname=form_data.fname.data,
                lname=form_data.lname.data,
                uname=form_data.uname.data,
                email=form_data.email.data,
                password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return True


def is_login_successful(form_data):

    email = form_data.email.data
    password = form_data.password.data

    user = User.query.filter_by(email=email).first()

    if user is not None:
        if bcrypt.check_password_hash(user.password, password):
            login_user(user)

            return True
    else:
        return False


if __name__ == "__main__":
    app.run(debug=True)
