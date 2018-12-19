'''
Created on 28 de feb. de 2018

@author: desweb
'''
# 1.system libraries
import os, sys
# 2.second part libraries
from flask import Flask,render_template, flash, request, url_for, redirect, session
from wtforms import Form, validators, StringField, PasswordField,SelectField as sf 
from wtforms.validators import DataRequired, Length, Email
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mail import Mail, Message
#from reportlab.pdfbase.pdfform import SelectField
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath


# 3 .my libraries
DES_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(DES_PATH)
from pg_operations2 import pg_operations2
from settings import settings

user = settings.USER
password = settings.PASSWORD
host = settings.HOST
port = settings.PORT
database = settings.DATABASE

app = Flask(__name__)

app.config.update(
    #EMAIL SETTINGS
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=465,
    MAIL_USE_SSL=True,
    MAIL_USERNAME = 'compruebaGaspar@gmail.com',
    MAIL_PASSWORD = 'gasparProject',
    MAIL_DEFAULT_SENDER ='SECURITY_EMAIL_SENDER'
    )

MAIL_SERVER='smtp.gmail.com',
MAIL_PORT=587,
MAIL_USE_TLS=True,
MAIL_USERNAME = 'compruebaGaspar@gmail.com',
MAIL_PASSWORD = 'gasparProject'
app.config['SECURITY_EMAIL_SENDER'] = 'compruebaGaspar@gmail.com'
mail = Mail(app)

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'uploads')
ALLOWED_EXTENSIONS = set(['png', 'jpg'])

#mail.init_app(app)
app.config['SECRET_KEY'] = 'super-secret'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SECURITY_REGISTERABLE'] = True
# additional configs:
app.config['SECURITY_PASSWORD_HASH'] = 'sha256_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'fhasdgihwntlgy8f'
app.config['SECURITY_RECOVERABLE'] = True
app.debug = True



@app.route('/')
def index():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return render_template("main.html")

@app.route('/map')
def map():
    return render_template("mapTrashReporter.html")


class RegistrationForm(Form):
    email = StringField('Email Address', [validators.Length(min=6, max=50),validators.DataRequired()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'), validators.Length(min=6, max=50)
    ])
    confirm = PasswordField('Repeat Password')
    choices = [('No','No'), ('Yes','Yes')]
    
    requestAccess= sf(u'No',choices=choices)


@app.route('/register', methods=['GET', 'POST'])
def register():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    form = RegistrationForm(request.form)
    try:        
        if request.method == 'POST' and form.validate():
            if 1==1:   
                email = form.email.data
                passwordUser = sha256_crypt.encrypt(form.password.data)
                cursor=d_conn['cursor']
                requestAccess =  form.requestAccess.data
                params = {
                    '_email' : email,
                    '_password' : passwordUser,
                    '_requestAccess' : requestAccess
                }
                query = """insert into d.user (email, encrypted_password, requestAccess) 
                 values (%(_email)s,%(_password)s, %(_requestAccess)s)"""
                cursor.execute(query, params)
                conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)

                #cursor.fetchall()                  
                flash('Thanks for registering!', 'success')
                return redirect(url_for('index'))
        return render_template('register.html', form=form)
    except:
        conn=d_conn['conn']
        conn.rollback()
        d_conn = pg_operations2.pg_disconnect2(d_conn)

        flash('ERROR! Email ({}) already exists.'.format(form.email.data), 'error')
        return render_template('register.html', form=form)


# Route for handling the login page logic
@app.route('/login', methods=['GET', 'POST'])
def login():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    if request.method == 'POST':
        # Get Form Fields
        email = request.form['email']
        password_candidate = request.form['password']

        
        data = cursor.execute("SELECT encrypted_password FROM d.user WHERE email = %s",[email])
        data = cursor.fetchone()[0]



        if sha256_crypt.verify(password_candidate, data):
            data = cursor.execute("SELECT remove_access FROM d.user WHERE email = %s",[email])
            data = cursor.fetchone()[0]

            if data:
                session['remove_access'] = True
            session['logged_in'] = True
            session['email'] = request.form['email']
            print session
            flash('You are now logged in', 'success')
            d_conn = pg_operations2.pg_disconnect2(d_conn)

            return redirect(url_for('index', email = session['email']))
        else:
            error = 'Invalid login'
            return render_template('login.html', error=error)
            # Close connection
            cursor.close()
            conn.close()
            d_conn = pg_operations2.pg_disconnect2(d_conn)


        d_conn = pg_operations2.pg_disconnect2(d_conn)
    

    return render_template('login.html')



# Check if user logged in
def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap



# Check if has access
def is_municipality(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'remove_access' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please CONTACT US for access', 'danger')
            return redirect(url_for('index'))
    return wrap


# Logout
@app.route('/logout/')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))



def send_async_email(msg):
    with app.app_context():
        mail.send(msg)

from threading import Thread


def send_email(subject, recipients, html_body):
    msg = Message(subject, recipients=recipients)
    #msg.body = text_body
    msg.html = html_body
    thr = Thread(target=send_async_email, args=[msg])
    thr.start()


class EmailForm(Form):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=6, max=40)])

from itsdangerous import  URLSafeTimedSerializer


def send_password_reset_email(user_email):
    password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    password_reset_url = url_for(
        'resetPass_with_token',
        token=password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
        _external=True)

    html = render_template(
        'email_password_reset.html',
        password_reset_url=password_reset_url)

    send_email('Password Reset Requested', [user_email], html)

@app.route('/reset-password', methods=('GET', 'POST',))
def forgot_password():
    token = request.args.get('token',None)
    form = EmailForm(request.form) #form
    if form.validate():
        email = form.email.data
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)

        conn=d_conn['conn']
        cursor=d_conn['cursor']
        cursor.execute("SELECT encrypted_password FROM d.user WHERE email = %s",[email])
        if cursor.fetchone() is None:
            print 0
            flash('Not such email.', 'error')
            return render_template('emailForgotPass.html', form=form)
        else:

            d_conn = pg_operations2.pg_disconnect2(d_conn)

            send_password_reset_email(email)
            flash('Please check your email for a password reset link.', 'success')
            return redirect(url_for('login'))
    return render_template('emailForgotPass.html', form=form)


class PasswordForm(Form):
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'), validators.Length(min=6, max=50)
    ])
    confirm = PasswordField('Repeat Password')


@app.route('/resetPassword/<token>', methods=['GET', 'POST'])
def resetPass_with_token(token):
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    try:
        form = PasswordForm(request.form)
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)

        if form.validate():
            if 1==1:
                
                password2 = sha256_crypt.encrypt(form.password.data)

                cursor=d_conn['cursor']

                cursor.execute("UPDATE d.user set encrypted_password = %s WHERE  email = %s;",[password2,email])

                conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)
    
                flash('Your password has been updated!', 'success')
                return redirect(url_for('login'))

        return render_template('emailForgotPassToken.html', form=form, token=token)

    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))

from datetime import datetime

class addPointForm(Form):
    lat = StringField('Latitude', [validators.DataRequired()])
    long = StringField('Longitude', [validators.DataRequired()])
    choices = [('Papier','Papier'),
               ('Restmuel','Restmuel'),
               ('Organisch','Organisch'),
               ('Wertsteff','Wertsteff'),
               ('Glass','Glass'),
               ('Restmuel','Restmuel'),
               ('Other','Other'),
                ('Mixed','Mixed')]
    
    trashType= sf(u'Mixed',choices=choices)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/addPoint', methods=['GET', 'POST'])
def upload_file():
        try:
            form = addPointForm(request.form)
            d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
            conn=d_conn['conn']
            cursor=d_conn['cursor']        
            if request.method == 'POST':
            # check if the post request has the file part
                if 'file' not  in request.files:

                    print 'no file'
                    return redirect(request.url)
                file = request.files['file']
                # if user does not select file, browser also
                # submit a empty part without filename
                if file.filename == '':
   

                    print 'no filename'

                if file and (file.filename.split(".")[1] == "jpeg" or file.filename.split(".")[1] == "jpg"):
                    print 1
                    filename = secure_filename(file.filename)
                    print 1

                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    print 1
                
                
                elif  file and (file.filename.split(".")[1] != "jpeg" or file.filename.split(".")[1] != "jpg"):
                    conn=d_conn['conn']
                    conn.rollback()
                    d_conn = pg_operations2.pg_disconnect2(d_conn)
        
                    flash('ERROR! Please uplod only JPEG.', 'error')
                    return render_template('registerTrashReporter..html', form = form) 
                
                elif file.filename  == None or file.filename  == '':
                    file.filename = ''
                    
                print 1    
                if form.validate():
                    filename = file.filename 
                    print filename  
                    lat = form.lat.data
                    long = form.long.data
                    trashType= form.trashType.data
                    dt = datetime.now()
                    
                    params = {
                        '_lat': lat,      
                        '_long' : long,
                        '_trashType' : trashType,
                        '_cp_file_name': filename,
                        '_trash_time': dt,
                    }
                    query = """insert into d.point
                    (latitude, longitude, geom, trash_type, cp_file_name, trash_time) 
                     values (%(_lat)s,%(_long)s,
                     ST_SetSRID(ST_MakePoint(%(_long)s, %(_lat)s), 3857),
                     %(_trashType)s, %(_cp_file_name)s, %(_trash_time)s)""" 
                    cursor.execute(query, params)
                    conn.commit()

                    d_conn = pg_operations2.pg_disconnect2(d_conn)                    
                    flash('Point uploaded', 'success')

                    return redirect(url_for('map'))

        except:
            conn=d_conn['conn']
            conn.rollback()
            d_conn = pg_operations2.pg_disconnect2(d_conn)

            flash('ERROR! Coords already exist.', 'error')
            return render_template('registerTrashReporter..html', form = form)                            
        return render_template('registerTrashReporter..html', form = form)
    

@app.route('/removePoint', methods=['GET', 'POST'])
@is_municipality
def removePoint():
    print 1
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor']
    cons='select COUNT(*) from d.point'
    cursor.execute(cons)
    lista = cursor.fetchall()
    cons="select timestamp without time zone 'epoch' + max(extract(epoch from trash_time)) * interval '1 second' from d.point"

    cursor.execute(cons)
    lista2 = cursor.fetchall()
    cons="select timestamp without time zone 'epoch' + min(extract(epoch from trash_time)) * interval '1 second' from d.point"
   
    cursor.execute(cons)
    lista3 = cursor.fetchall()
    cons="select timestamp without time zone 'epoch' + avg(extract(epoch from trash_time)) * interval '1 second' from d.point"
    cursor.execute(cons)
    lista4 = cursor.fetchall()
    time = None
    for i in lista4:
        time = str(i[0])
   
    lista4 =  time[11:19] 
    cons='select trash_type, count(trash_type) from d.point group by trash_type order by trash_type;'    
    cursor.execute(cons)
    lista5= cursor.fetchall()
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    

    return render_template("statsTrashReporter.html", lista=lista, lista2=lista2
                           ,lista3=lista3,lista4=lista4, lista5=lista5
                            )
@app.route('/stats')
@is_logged_in
def stats():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor']
    cons='select COUNT(*) from d.point'
    cursor.execute(cons)
    lista = cursor.fetchall()
    cons="select timestamp without time zone 'epoch' + max(extract(epoch from trash_time)) * interval '1 second' from d.point"

    cursor.execute(cons)
    lista2 = cursor.fetchall()
    cons="select timestamp without time zone 'epoch' + min(extract(epoch from trash_time)) * interval '1 second' from d.point"
   
    cursor.execute(cons)
    lista3 = cursor.fetchall()
    cons= "select timestamp without time zone 'epoch' + (max(extract(epoch from trash_time)) - min(extract(epoch from trash_time))) * interval '1 second' from d.point"
    cursor.execute(cons)
    lista4 = cursor.fetchall()
    time = None
    for i in lista4:
        time = str(i[0])
   
    lista4 =  time[11:19] 
    cons='select trash_type, count(trash_type) from d.point group by trash_type order by trash_type;'    
    cursor.execute(cons)
    lista5= cursor.fetchall()
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    

    return render_template("statsTrashReporter.html", lista=lista, lista2=lista2
                           ,lista3=lista3,lista4=lista4, lista5=lista5
                            )




if __name__ == '__main__':
    app.run()
