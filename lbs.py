'''
@author: desweb
'''
# 1.system libraries
import os, sys
# 2.second part libraries
from flask import Flask,render_template, flash, request, url_for, redirect, session, jsonify
from wtforms import Form, validators, StringField, PasswordField,SelectField as sf
from wtforms.validators import DataRequired, Length, Email
from passlib.hash import sha256_crypt
from functools import wraps
from flask_mail import Mail, Message
#from reportlab.pdfbase.pdfform import SelectField
from datetime import datetime
from geopy.geocoders import Nominatim

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
    MAIL_USERNAME = 'xxxxxx@gmail',
    MAIL_PASSWORD = 'xxxxxxxxxxxxx',
    MAIL_DEFAULT_SENDER ='SECURITY_EMAIL_SENDER'
    )

MAIL_SERVER='smtp.gmail.com',
MAIL_PORT=587,
MAIL_USE_TLS=True,
MAIL_USERNAME = 'xxxxxxxxxxx@gmail',
MAIL_PASSWORD = 'xxxxxxxx'
app.config['SECURITY_EMAIL_SENDER'] = 'xxxxxxx@gmail.com'
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
    email = StringField('Email Address', [validators.Length(min=6, max=50),validators.DataRequired(), Email()])
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
    cursor=d_conn['cursor'] 
    cursor.execute("select choice from d.choices")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    return choices

def dbCountryChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor'] 
    cursor.execute("select distinct(country_name) from countries where country_name != '' order by country_name")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return choices

def dbCountryChoicesEmpty():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor'] 
    cursor.execute("select distinct(country_name) from countries order by country_name")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return choices


@app.route('/dbProductChoices', methods=('GET', 'POST',))
def dbProductChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor'] 
    cursor.execute("select product from products")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return choices




def dbVegChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor'] 
    cursor.execute("select veg from veg")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return choices

def dbMaleChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor'] 
    cursor.execute("select gender from gender")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return choices



# Check if has access
def is_municipality(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'remove_access' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please CONTACT US for access', 'danger')
            return redirect(url_for('map'))
    return wrap




class touristForm(Form):
    city = StringField('Tourist city')
    tops = dbProductChoices()
    top1=sf(tops[0],choices=tops)
    top2=sf(tops[0],choices=tops)
    top3=sf(tops[0],choices=tops)
    lastTrips = dbCountryChoicesEmpty()
    last_trip = sf(lastTrips[0],choices=lastTrips)
    next_trip = sf(lastTrips[0],choices=lastTrips)
    age = StringField('Tourist age')                 
    maxbudget = StringField('Tourist budget')
    vegeterian = dbVegChoices()
    veg= sf(vegeterian[0],choices=vegeterian)
    countries =  dbCountryChoices()
    country= sf(countries[0],choices=countries)
    genders = dbMaleChoices()
    gender= sf(genders[0],choices=genders)
 
    

def paramsTouristInsert(country, city, top1, top2, top3, age, maxbudget, veg,  gender, last_trip, next_trip):
    params = {          
                        '_country': country,
                        '_city': city,
                        '_top1': top1,
                        '_top2': top2,
                        '_top3': top3,

                        '_age': age,
                        '_maxbudget': maxbudget,
                        '_veg':  veg,
                        '_gender': gender,
                        '_last_trip': last_trip,
                        '_next_trip': next_trip
                        }
     
    return params

def queryTouristInsert():
    query = """insert into d.tourist
                    ( country, city, top1, top2, top3, age, maxbudget, veg,  gender, last_trip
                    , next_trip) 
                    values(
                      
                      %(_country)s, %(_city)s, %(_top1)s, %(_top2)s,%(_top3)s, %(_age)s,
                      %(_maxbudget)s, %(_veg)s ,%(_gender)s, %(_last_trip)s, %(_next_trip)s)""" 
                     
    return query 


@app.route('/addTourist', methods=['GET', 'POST'])
def upload_file_tourist():
        try:
            form = touristForm(request.form)
            d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
            conn=d_conn['conn']
            cursor=d_conn['cursor']
              
            if request.method == 'POST':  
                if form.validate():
                    country = form.country.data
                    city = form.city.data
                    age = form.age.data
                    maxbudget = form.maxbudget.data
                    top1 = form.top1.data
                    top2 = form.top2.data
                    top3 = form.top3.data
                    last_trip = form.last_trip.data
                    next_trip = form.next_trip.data
                    veg = form.veg.data
                    gender = form.gender.data                    
                    params = paramsTouristInsert(country, city, top1, top2, top3, age, maxbudget, veg,  gender, last_trip, next_trip)                    
                    query = queryTouristInsert()
                    cursor.execute(query, params)
                    conn.commit()
                    d_conn = pg_operations2.pg_disconnect2(d_conn)                    
                    flash('Tourist uploaded', 'success')
                    return redirect(url_for('map'))

        except:
            conn=d_conn['conn']
            conn.rollback()
            d_conn = pg_operations2.pg_disconnect2(d_conn)

            flash('ERROR! ', 'danger')
            return render_template('addTourist.html', form = form) 
        return render_template('addTourist.html', form = form)   
             
class addPointForm(Form):
    lat = StringField('Latitude')
    lon = StringField('longitude')
    supermarket_name = StringField('Supermarket name', [validators.DataRequired()])
    phone = StringField('Phone number')
    email = StringField('Email', [Email()])
    web = StringField('Web')
    contact_person = StringField('Contact person at the supermarket')
    first_contact = StringField('First contact person at the supermarket')
    last_contact = StringField('Last contact person at the supermarket')
    outdoor_person = StringField('Outdoor person assigned to this supermarket')
    superAddress = StringField('Address of the supermarket')
    choices = dbCustChoices()
    choice= sf(choices[0],choices=choices)



    


def paramsInsert(lat, lon, supermarket_name,  address, phone, email,web , contact_person,
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
                    geolocator = Nominatim(user_agent="app")

 
                    if form.lat.data == '' or form.lat.data is None or form.lon.data == '' or form.lon.data is None:
                        location = geolocator.geocode(form.superAddress.data)
                        address = form.superAddress.data
                        lat = location.latitude
                        lon = location.longitude
                    else:    
                        lat = form.lat.data
                        lon = form.lon.data
                        address = nominatim(str(lat), str(lon))
                    checkPol(lat, lon, form)
                    supermarket_name = form.supermarket_name.data
                    phone = form.phone.data
                    email = form.email.data
                    web = form.web.data
                    contact_person = form.contact_person.data
                    custEvaluation= form.choice.data
                    fk_customer_importance_evaluation = fkEvluation(custEvaluation)
                    
                    first_contact = form.first_contact.data  
                    last_contact = form.last_contact.data     
                    outdoor_person = form.outdoor_person.data
                    params = paramsInsert(lat, lon, supermarket_name, 
                    address, phone, email, web, contact_person,
                    fk_customer_importance_evaluation,
                    first_contact, last_contact, outdoor_person)
                    print params
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
          
@app.route('/removePoint', methods=['GET', 'POST'])
@is_municipality
def removePoint():
        return render_template("mapLBSRemove.html")

@app.route('/interactive/')
def interactive():
        lista = []
        dict = {}
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
        conn=d_conn['conn']
        cursor=d_conn['cursor']
        data = cursor.execute("SELECT  gid, st_astext(geom), address FROM d.supermarket")
        data = cursor.fetchall()
        print data
        for row in data:
            gid = row[0]
            geom = row[1]
            address = row[2]
            meas = {"gid": gid, "geom": geom, "address":address}
            lista.append(meas)
            dict["data"]=lista
        #print dict    
        d_conn = pg_operations2.pg_disconnect2(d_conn)
        return jsonify(dict)



@app.route('/deleteRowSim/<gid>', methods=('GET', 'POST',))
def deleteRowSim(gid):
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    cursor.execute("DELETE FROM d.supermarket WHERE gid = %s",[gid])
    conn.commit()
    data = interactive2()
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return data   

       


@app.route('/stats')
@is_logged_in
def stats():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor']  
    cons="""select COUNT(gid),
      timestamp without time zone 'epoch' + max(extract(epoch from created_at)) * interval '1 second',
       timestamp without time zone 'epoch' + min(extract(epoch from created_at)) * interval '1 second'
        from d.supermarket"""
    cursor.execute(cons)
    data = cursor.fetchall()
    for i in data:
        counter = i[0]
        maxTime = str(i[1])
        minTime = str(i[2]) 
    maxTime =  str(maxTime[:19]) 
    fmt = '%Y-%m-%d %H:%M:%S'
    maxTime = datetime.strptime(maxTime, fmt)
    minTime =  str(minTime[:19]) 
    minTime = datetime.strptime(minTime, fmt)
    timeDiff = str(maxTime - minTime)
    lista = []
    lista2 = []
    dict = {}
    cons = """
    select a.choice, count(b.fk_customer_importance_evaluation) 
    from d.choices AS a INNER JOIN d.supermarket AS b
    ON a.id = b.fk_customer_importance_evaluation
    group by a.choice, b.fk_customer_importance_evaluation
    order by b.fk_customer_importance_evaluation
    """    
    cursor.execute(cons)
    for i in cursor.fetchall():
        superMarketType = i[0]
        superMarketCounter = i[1]  
        lista2.append(superMarketType) 
        lista2.append(superMarketCounter)  
    meas = {"counter": counter, "maxTime": maxTime, "minTime":minTime, "timeDiff":timeDiff,
             "lista2":lista2}
    lista.append(meas)
    dict["data"]=lista
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return jsonify(dict)

@app.route('/statistics')
@is_logged_in
def statistics():
    return render_template("statsLBS.html")
       
       
          
if __name__ == '__main__':
    app.run()
