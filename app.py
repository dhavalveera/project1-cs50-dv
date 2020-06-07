import os
import requests
import json
from flask import Flask, session, render_template, redirect, request, flash, url_for
from flask_bcrypt import Bcrypt
from forms import SignUp, Login, searchBook, bookReview
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"), encoding="utf8")
db = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)
bcrypt = Bcrypt(app)
app.config['SECRET_KEY'] = 'my123secret456key789'

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)




@app.route('/', methods=['GET', 'POST'])
def index():

    user_id = session.get('u_id')
    if user_id:
        return redirect(url_for('dashboard'))

    form_one = SignUp()

    if form_one.validate_on_submit():
        fname = form_one.fname.data
        email = form_one.email.data
        username = form_one.username.data
        password = form_one.password.data

        hash_password = bcrypt.generate_password_hash(password).decode('utf-8')

        user = db.execute("SELECT * FROM reg_accounts WHERE email = :email", {"email" : email}).fetchone()

        db.execute("INSERT INTO reg_accounts (fname, username, email, password) VALUES (:fname, :username, :email, :password)", {"fname" : fname, "username" : username, "email" : email, "password" : hash_password})
        db.commit()

        flash(f'Your Account has been registered successfully, you can now login.', 'success')

        return redirect(url_for('index'))


    form_two = Login()

    if form_two.validate_on_submit():
        username_two = form_two.username_two.data
        password = form_two.password.data

        user = db.execute("SELECT * FROM reg_accounts WHERE username = :username", {"username" : username_two}).fetchone()

        if user and bcrypt.check_password_hash(user.password, password) is True:
            session['u_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash(f'You have entered incorrect Email ID or Password, please check your entered Email ID/Password.', 'warning')
            return redirect(url_for('index'))

    return render_template('index.html', form_one=form_one, form_two=form_two)


@app.route('/logout', methods=['GET', 'POST'])
def logout():
    session.pop('u_id', None)

    flash(f'You have logout successfully.', 'success')

    return redirect(url_for('index'))



@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():

    bookForm = searchBook()

    if bookForm.validate_on_submit():
        isbnNum = bookForm.isbnNum.data
        title = bookForm.title.data
        author = bookForm.author.data

        bookdetail = db.execute("SELECT * FROM books WHERE isbn LIKE :isbn AND title LIKE :title AND author LIKE :author", {"isbn" : f'%{isbnNum}%', "title" : f'%{title}%', "author" : f'%{author}%'}).fetchall()
        print(bookdetail)
        return render_template('dashboard.html', bookForm=bookForm, bookdetail=bookdetail)

    return render_template('dashboard.html', bookForm=bookForm)

@app.route('/dashboard/<string:searchbooks_isbn>', methods=['GET', 'POST'])
def dashboards(searchbooks_isbn):

    session['selectedISBN'] = searchbooks_isbn
    dashboards = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn" : searchbooks_isbn}).fetchone()

    bookrv = bookReview()

    if bookrv.validate_on_submit():
        rating = bookrv.rating.data
        comment = bookrv.comment.data

        db.execute("INSERT INTO bookreview (isbn, rating, comment) VALUES (:isbn, :rating, :comment)", {"isbn" : searchbooks_isbn,"rating" : rating, "comment" : comment})
        db.commit()

        flash(f'Your Review has successfully submitted.', 'success')

    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "eljwzFz3AzOOQBw3qMnIBg", "isbns": searchbooks_isbn})

    goodreadsAvg = ""
    goodreadsWRC = ""

    if res.status_code == 200:
        goodreads = res.json()['books']
        goodreadsAvg = goodreads[0]['average_rating']
        goodreadsWRC = goodreads[0]['work_ratings_count']


    values = {
        "goodreadsAvg" : goodreadsAvg,
        "goodreadsWRC" : goodreadsWRC
    }

    user_comment = db.execute("SELECT * FROM bookreview WHERE isbn = :isbn", {"isbn" : searchbooks_isbn}).fetchall()

    return render_template('books_list.html', dashboards=dashboards, bookrv=bookrv, values=values, user_comment=user_comment)


@app.route('/api/<string:search_isbn>', methods=['GET'])
def api(search_isbn):

    get_detail_one = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn" : search_isbn}).fetchone()

    if get_detail_one is None:
        raise Exception('404 Not Found')


    avgscore = db.execute("SELECT AVG(rating) FROM bookreview WHERE isbn = :isbn", {"isbn" : search_isbn})
    rating = (float(avgscore.fetchone()[0]))

    rcount = db.execute("SELECT COUNT(comment) FROM bookreview WHERE isbn = :isbn", {"isbn" : search_isbn})
    recount = (rcount.fetchone()[0])




    bookApi = {
        "title": get_detail_one.title,
        "author": get_detail_one.author,
        "year": get_detail_one.year,
        "isbn": get_detail_one.isbn,
        "review_count": recount,
        "average_score": rating
    }

    return json.dumps(bookApi)
