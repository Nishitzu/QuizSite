from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import User, Scoreboard
from . import db #importing db from __init__.py
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import login_user, login_required, logout_user, current_user


#Utility
def validation_checks(email, username, passwd, passwdck):
    validation_dict = {}
    nameExists = db.session.query(User.id).filter_by(username=username).first() is not None
    mailExists = db.session.query(User.id).filter_by(email=email).first() is not None

    if len(email) < 6 and "@" not in email:
        validation_dict["message"] = "L'email ha un formato non corretto"
        validation_dict["category"] = 'error'
        validation_dict["insertUser"] = False
    elif len(username) < 2:
        validation_dict["message"] = "Lo username ha un formato non corretto"
        validation_dict["category"] = 'error'
        validation_dict["insertUser"] = False
    elif passwd != passwdck:
        validation_dict["message"] = "Le due password non coincidono"
        validation_dict["category"] = 'error'
        validation_dict["insertUser"] = False
    elif len(passwd) < 6:
        validation_dict["message"] = "La password deve contenere almeno 6 caratteri"
        validation_dict["category"] = 'error'
        validation_dict["insertUser"] = False
    elif nameExists or mailExists:
        validation_dict["message"] = "L'email o lo username sono già registrati"
        validation_dict["category"] = 'error'
        validation_dict["insertUser"] = False
    else:
        validation_dict["message"] = ""
        validation_dict["category"] = ''
        validation_dict["insertUser"] = True

    return validation_dict


auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        #userData = request.form (Utility ImmutableMultiDict)
        email = request.form.get('email')
        passwd = request.form.get('password')

        user = User.query.filter_by(email = email).first() #using another query method to showcase different approaches
        if user:
            if check_password_hash(user.password, passwd):
                login_user(user, remember=True) #remembers user log in until the user clears cache or webserver restars
                return redirect(url_for('views.home'))
            else:
                flash("Password non corretta, perfavore riprova", category='error')
        else:
            flash("L'utente inserito non esiste, prima creare un account", category='error')

    return render_template("login.html")

@auth.route('/logout')
@login_required #decorator, prevents user from access this route unless the user is logged in
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        #userData = request.form (Utility ImmutableMultiDict)
        email = request.form.get('email')
        username = request.form.get('username')
        passwd = request.form.get('password')
        passwdck = request.form.get('passwdcheck')

        checkDict = validation_checks(email, username, passwd, passwdck)

        if checkDict["insertUser"] == False:
            flash(checkDict["message"], category=checkDict["category"])
        elif checkDict["insertUser"] == True:
            new_user = User(username=username, email=email, password=generate_password_hash(passwd, method='pbkdf2:sha1', salt_length=8))
            db.session.add(new_user)
            db.session.flush()

            new_score = Scoreboard(userId=new_user.id, userScore=0)
            db.session.add(new_score)

            db.session.commit()

            #another approach to validation of duplicate username or email is to let the database check for Integrity on "unique" fields
            #I prefer to explicitly query the database where possible to avoid unclear exceptions
            #try:
                #session.add(item)
                #session.flush()
            #except exc.IntegrityError:
                #session.rollback()
            #db.session.commit()

            checkDict["insertUser"] = False
            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))
        else:
            flash("Qualcosa è andato storto! Ricarica la pagina!", category='error')


    return render_template("register.html")