'''
@author: desweb
'''
# 1.system libraries
import os, sys
# 2.second part libraries
from flask import Flask,render_template, flash, request, url_for, redirect, session, jsonify
from wtforms import Form, validators, StringField, PasswordField,SelectField as sf, FloatField 
from wtforms.validators import DataRequired, Length, Email
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mail import Mail, Message
#from reportlab.pdfbase.pdfform import SelectField
from werkzeug.utils import secure_filename
from os.path import join, dirname, realpath
import json
from datetime import datetime
from geopy.geocoders import Nominatim
import geojson
import uuid
from fileinput import filename
# 3 .my libraries
DES_PATH = os.path.dirname(os.path.dirname(__file__))
sys.path.append(DES_PATH)
from pg_operations2 import pg_operations2
from settings import settingsLBS

user = settingsLBS.USER
password = settingsLBS.PASSWORD
host = settingsLBS.HOST
port = settingsLBS.PORT
database = settingsLBS.DATABASE

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



#mail.init_app(app)
app.config['SECRET_KEY'] = 'super-secret'

app.config['SECURITY_REGISTERABLE'] = True
# additional configs:
app.config['SECURITY_PASSWORD_HASH'] = 'sha256_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'fhasdgihwntlgy8f'
app.config['SECURITY_RECOVERABLE'] = True
app.debug = True



@app.route('/')
def index():

    return render_template("indexLBS.html")

@app.route('/map')
def map():

    return render_template("mapLBS.html")

def dbAccessChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor'] 
    cursor.execute("select acess_type from d.remove_access")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    choices =  (choices[0], choices[1])    
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    return choices 


class RegistrationForm(Form):
    email = StringField('Email Address', [validators.Length(min=6, max=50),validators.DataRequired()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'), validators.Length(min=6, max=50)
    ])
    confirm = PasswordField('Repeat Password')
    choices = dbAccessChoices()
    
    requestAccess= sf(choices[0],choices=choices)

def paramsRegister(email, passwordUser, fk_request_access):
    
    params = {
        '_email' : email,
        '_password' : passwordUser,
        '_fk_request_access' : fk_request_access,
        }
    return params

def queryRegister():
    query = """insert into d.user (email, encrypted_password, fk_request_access) 
                 values (%(_email)s,%(_password)s, %(_fk_request_access)s)"""
    return query

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
                if requestAccess == 'No':
                    fk_request_access = 1
                else: 
                    fk_request_access = 0 
                params = paramsRegister(email, passwordUser, fk_request_access)      
                query = queryRegister()
                cursor.execute(query, params)
                conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)
                newUserEmail(email)

                flash('Thanks for registering! Please approve your registration via email', 'success')
                return redirect(url_for('index'))
        return render_template('registerLBS.html', form=form)
    except:
        conn=d_conn['conn']
        conn.rollback()
        d_conn = pg_operations2.pg_disconnect2(d_conn)

        flash('ERROR! Email ({}) already exists.'.format(form.email.data), 'danger')
        return render_template('registerLBS.html', form=form)


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
            flash('You are now logged in as ' + email, 'success')
            d_conn = pg_operations2.pg_disconnect2(d_conn)

            return redirect(url_for('index', email = session['email']))
        else:
            error = 'Invalid login'
            return render_template('loginLBS.html', error=error)
            # Close connection
            cursor.close()
            conn.close()
            d_conn = pg_operations2.pg_disconnect2(d_conn)


        d_conn = pg_operations2.pg_disconnect2(d_conn)
    

    return render_template('loginLBS.html')



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
    
    
def newUserEmail(user_email):
    password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])

    password_reset_url = url_for(
        'confirmUser_with_token',
        token=password_reset_serializer.dumps(user_email, salt='password-reset-salt'),
        _external=True)

    html = render_template(
        'newUserConf.html',
        password_reset_url=password_reset_url)

    send_email('Confirmation Requested', [user_email], html)
    


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
            flash('Not such email.', 'danger')
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
    
                flash('Your profile has been confirmed!', 'success')
                return redirect(url_for('login'))

        return render_template('emailForgotPassToken.html', form=form, token=token)

    except:
        flash('The link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))
    

@app.route('/confirmUser/<token>', methods=['GET', 'POST'])
def confirmUser_with_token(token):
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    try:
        form = PasswordForm(request.form)
        password_reset_serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
        print 1
        #if form.validate():
        if 1==1:
                
                #password2 = sha256_crypt.encrypt(form.password.data)

                cursor=d_conn['cursor']

                cursor.execute("UPDATE d.user set confirmed = True WHERE  email = %s;",[email])
                print 1
                conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)
    
                flash('Your password has been updated!', 'success')
                return redirect(url_for('login'))

        return render_template('newUser_withToken.html', form=form, token=token)

    except:
        flash('The password reset link is invalid or has expired.', 'danger')
        return redirect(url_for('login'))    


def checkPol(lat, lon, form):
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor'] 
    cursor.execute("select min(st_y(geom)),max(st_y(geom)),min(st_x(geom)),max(st_x(geom)) from gis_osm_places_free_1")
    data = cursor.fetchall()
    for row in data:
        minX =  row[0]
        maxX = row[1]
        minY = row[2]
        maxY = row[3]
    if lat < minX or lat > maxX or lon < minY or lon > maxY:
        conn.rollback()
        d_conn = pg_operations2.pg_disconnect2(d_conn)
    
        flash('ERROR! Coords are out of Karlsruhe.', 'danger')
        return render_template('registerTrashReporter..html', form = form)
    d_conn = pg_operations2.pg_disconnect2(d_conn)    


        
def fkEvluation(custEvaluation):
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor'] 
    cursor.execute("select id from d.choices where choice = %s",[custEvaluation])
    fk_customer_importance_evaluation = cursor.fetchall() 
    for row in fk_customer_importance_evaluation:
        fk_customer_importance_evaluation = row[0]
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    return  fk_customer_importance_evaluation  

    
def nominatim(lat, lon):
    geolocator = Nominatim(user_agent="app")
    location = geolocator.reverse(str(lat) + ", " + str(lon))
    if location.address is None or location.address  == '':
        address = 'Unknown'
    else:
        address = location.address.split(',')[0] + ", " \
        + location.address.split(',')[1] + ", " \
        +location.address.split(',')[2] + ", " \
        +location.address.split(',')[3] + ", " \
        +location.address.split(',')[4] 
    return address

def dbCustChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor'] 
    cursor.execute("select choice from d.choices")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    return choices


class addPointForm(Form):
    lat = FloatField('Latitude', [validators.DataRequired()])
    lon = FloatField('longitude', [validators.DataRequired()])
    supermarket_name = StringField('Supermarket name', [validators.DataRequired()])
    phone = StringField('Phone number')
    email = StringField('Email')
    web = StringField('Web')
    contact_person = StringField('Contact person at the supermarket')
    first_contact = StringField('First contact person at the supermarket')
    last_contact = StringField('Last contact person at the supermarket')
    outdoor_person = StringField('Outdoor person assigned to this supermarket')
    choices = dbCustChoices()
    choice= sf(choices[0],choices=choices)
    


def paramsInsert(lat, lon, supermarket_name, address, phone, email,web , contact_person,
                 fk_customer_importance_evaluation, first_contact,
                 last_contact, outdoor_person):
    params = {
                        '_lat': lat,      
                        '_lon' : lon,
                        '_supermarket_name': supermarket_name,
                        '_address': address,
                        '_phone' : phone,
                        '_email':email,
                        '_web':web,
                        '_contact_person':contact_person,
                        '_fk_customer_importance_evaluation':fk_customer_importance_evaluation,
                        '_first_contact':first_contact,
                        '_last_contact':last_contact,
                        '_outdoor_person':outdoor_person
                         
                    }
     
    return params

def queryInsert():
    query = """insert into d.supermarket
                    (geom, supermarket_name, address, phone,
                     email,web, contact_person,
                     fk_customer_importance_evaluation,first_contact,
                     last_contact, outdoor_person) 
                    values(
                     ST_SetSRID(ST_MakePoint(%(_lat)s, %(_lon)s), 4326) 
                     , %(_supermarket_name)s, %(_address)s, %(_phone)s
                     , %(_email)s, %(_web)s, %(_contact_person)s,
                     %(_fk_customer_importance_evaluation)s,
                     %(_first_contact)s, %(_last_contact)s, %(_outdoor_person)s)""" 
                     
    return query


@app.route('/addPoint', methods=['GET', 'POST'])
def upload_file():
        try:

            form = addPointForm(request.form)
            d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
            conn=d_conn['conn']
            cursor=d_conn['cursor']  
            if request.method == 'POST':  
                if form.validate():
 
                    lat = form.lat.data
                    lon = form.lon.data
                    checkPol(lat, lon, form)
                    supermarket_name = form.supermarket_name.data
                    phone = form.phone.data
                    email = form.email.data
                    web = form.web.data
                    contact_person = form.contact_person.data
                    custEvaluation= form.choice.data
                    fk_customer_importance_evaluation = fkEvluation(custEvaluation)
                    address = nominatim(str(lat), str(lon))
                    first_contact = form.first_contact.data  
                    last_contact = form.last_contact.data     
                    outdoor_person = form.outdoor_person.data
                    params = paramsInsert(lat, lon, supermarket_name,
                    address, phone, email, web, contact_person,
                    fk_customer_importance_evaluation,
                    first_contact, last_contact, outdoor_person)
                    query = queryInsert()
                    cursor.execute(query, params)
                    conn.commit()
                    d_conn = pg_operations2.pg_disconnect2(d_conn)                    
                    flash('Point uploaded', 'success')
                    return redirect(url_for('map'))

        except:
            conn=d_conn['conn']
            conn.rollback()
            d_conn = pg_operations2.pg_disconnect2(d_conn)

            flash('ERROR! Coords already exist', 'danger')
            return render_template('addSupermarket.html', form = form)                            
        return render_template('addSupermarket.html', form = form)

      

@app.route('/background_process')
def background_process():
    try:
        lang = request.args.get('proglang', 0, type=str)
        
        return jsonify(result=lang )
    except Exception as e:
        return str(e)
    
       
def geoJsonMaker(x,y, address): 
      
    data = [     {
              "type": "Feature",
              "geometry": {
                "type": "Point",
                "coordinates": [lon,lat]
              },
              "properties": {
                "name": address
              }
            } for lon,lat, address in zip(y,x, address)]
    return data
    
  
@app.route('/interactive2/')
def interactive2():
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
        conn=d_conn['conn']
        cursor=d_conn['cursor']
        cursor.execute("SELECT st_y(geom), st_x(geom), address FROM d.supermarket")
        data = cursor.fetchall()
        x = []
        y = []
        address = []
        for row in data:
            x.append(row[0])
            y.append(row[1])
            address.append(row[2])
        data = geoJsonMaker(x,y, address)    
        d_conn = pg_operations2.pg_disconnect2(d_conn)
        return jsonify(data)    
          
if __name__ == '__main__':
    app.run()
