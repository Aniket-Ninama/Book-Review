from flask import render_template, request, url_for, redirect, Flask, flash
from flask_login import login_user, LoginManager, current_user, logout_user, login_required
from flask_bcrypt import Bcrypt
from extension import db
from dotenv import load_dotenv
import os
import requests
import smtplib
from email.mime.text import MIMEText
from models import Books, Registered_Users

load_dotenv()
api_key = os.getenv("API_KEY")
email=os.getenv("from_email")
password=os.getenv("from_password")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv("Secret_key")
db.init_app(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(Registered_Users, int(user_id))

@app.route('/', methods=["GET","POST"])
def login_page():
    if request.method == "POST":
        user_email = request.form["email"]
        log_password = request.form["password"]
        user_detail = db.session.execute(db.select(Registered_Users).where(Registered_Users.email == user_email)).scalar()
        if not user_detail:
            flash("Sorry we cannot find this email.")
            return redirect(url_for('signup_page'))
        elif not bcrypt.check_password_hash(user_detail.password, log_password):
            flash("Incorrect password, please try again.")
            return redirect(url_for('login_page'))
        else:
            login_user(user_detail)
            return redirect(url_for('index_page'))
    return render_template('login.html')

@app.route('/signup', methods=['GET', "POST"])
def signup_page():
    if request.method == "POST":
        if not db.session.execute(db.select(Registered_Users).where(Registered_Users.email == request.form["email"])).scalar():
            N_user_name = request.form['name']
            N_user_email = request.form['email']
            N_user_pass = request.form['password']
            bcrypt_pass = bcrypt.generate_password_hash(N_user_pass).decode('utf-8')
            new_user = Registered_Users(name=N_user_name, email=N_user_email, password=bcrypt_pass)
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user)
            return redirect(url_for('index_page'))
        else:
            flash("You've already signed up with that email, login in instead!")
            return redirect(url_for('login_page'))
    return render_template('signup.html')

@app.route('/home')
@login_required
def index_page():
    return render_template('index.html', user_books=current_user.saved_books)

@app.route('/explore', methods=['GET', 'POST'])
@login_required
def explore_page():
    url = "https://gutendex.com/books/"
    if request.method == 'POST':
        params = {"search": request.form["book_name"]}
        result = requests.get(url, params=params).json()["results"]
        return render_template('explore.html', books=result, book_name=request.form["book_name"])
    params = {"sort": "downloads"}
    books_details = requests.get(url, params).json()["results"][:30]
    return render_template('explore.html', books=books_details)

@app.route('/add_book')
@login_required
def add_book_page():
    book_title = request.args.get('title')
    book_author = request.args.get('author')
    book_cover = request.args.get('img')
    book_readers = request.args.get('downloads')
    existing_book = db.session.query(Books).filter_by(title=book_title, author=book_author).first()
    if not existing_book:
        new_book = Books(title=book_title, author=book_author, download_count=book_readers, book_img=book_cover)
        db.session.add(new_book)
        db.session.commit()
        current_user.saved_books.append(new_book)
    else:
        # Add existing book to current user's saved list if not already added
        if existing_book not in current_user.saved_books:
            current_user.saved_books.append(existing_book)
    db.session.commit()
    return redirect(url_for('index_page'))

@app.route('/remove_book')
@login_required
def remove_book_page():
    book_id = request.args.get('book_id')
    remove_book = db.session.execute(db.select(Books).where(Books.id == book_id)).scalar()
    db.session.delete(remove_book)
    db.session.commit()
    if remove_book in current_user.saved_books:
        current_user.saved_books.remove(remove_book)
        db.session.commit()
    return redirect(url_for('index_page'))

@app.route('/contact', methods=['GET','POST'])
@login_required
def contact_page():
    if request.method == "POST":
        user_name = request.form['name']
        user_email = request.form['email']
        message = request.form['message']
        msg_body = f"""
        From: {user_name}
        Email: {user_email}
        Message: {message}
        """
        msg = MIMEText(msg_body)
        msg["Subject"] = "New Contact Form Submission"
        msg["From"] = email
        msg["To"] = "aniketninama5@gmail.com"
        with smtplib.SMTP("smtp.gmail.com", 587) as connection:
            connection.starttls()
            connection.login(user=email, password=password)
            connection.send_message(msg)
        return render_template('contact.html', suceess=True)
    return render_template('contact.html', suceess=False)

@app.route('/logout')
@login_required
def logout_page():
    logout_user()
    return redirect(url_for('login_page'))

if __name__ == "__main__":
    app.run(debug=True)