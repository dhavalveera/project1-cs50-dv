import os
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, SubmitField
from wtforms.fields.html5 import EmailField, TelField
from wtforms.validators import DataRequired, Email, Length, InputRequired, ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine(os.getenv("DATABASE_URL"), encoding="utf8")
db = scoped_session(sessionmaker(bind=engine))


class SignUp(FlaskForm):
    fname = StringField('Enter your Name', validators=[DataRequired(), Length(max=25)])
    email = EmailField('Enter Email ID', validators=[DataRequired(), Email(message='Invalid Email')])
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Enter Password', validators=[DataRequired(), Length(min=8, max=16)])
    submit = SubmitField('Submit')

    def validate_email(self, email):
        user = db.execute("SELECT * FROM reg_accounts WHERE email = :email", {"email" : email.data}).fetchone()

        if user:
            raise ValidationError('This Email ID is already registered with us.')


class Login(FlaskForm):
    username_two = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Enter Password', validators=[DataRequired(), Length(min=8, max=16)])
    submit = SubmitField('Submit')



class searchBook(FlaskForm):
    isbnNum = StringField('ISBN Number')
    title = StringField('Book Title')
    author = StringField('Author Name')
    submit = SubmitField('Search')



class bookReview(FlaskForm):
    rating = SelectField('Rating', choices=[(' ', ' '), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')])
    comment = TextAreaField('Write your Comment', validators=[DataRequired(), Length(max=250)])
    submit = SubmitField('Submit Review')
