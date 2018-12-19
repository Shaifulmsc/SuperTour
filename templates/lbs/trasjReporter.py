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
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'gif', 'tif'])

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

    return render_template("main.html")

@app.route('/map')
def map():
    print request.get_data()

    return render_template("mapTrashReporter.html")

def dbAccessChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor'] 
    cursor.execute("select acess_type from d.remove_access")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    choices =  (choices[2], choices[1])    
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
    #choices = [('No','No'), ('Yes','Yes')]
    
    requestAccess= sf(choices[1],choices=choices)

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
                    fk_request_access = 3
                else: 
                    fk_request_access = 2 
                params = paramsRegister(email, passwordUser, fk_request_access)      
                query = queryRegister()
                cursor.execute(query, params)
                conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)
                newUserEmail(email)

                flash('Thanks for registering! Please approve your registration via email', 'success')
                return redirect(url_for('index'))
        return render_template('register.html', form=form)
    except:
        conn=d_conn['conn']
        conn.rollback()
        d_conn = pg_operations2.pg_disconnect2(d_conn)

        flash('ERROR! Email ({}) already exists.'.format(form.email.data), 'danger')
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
            flash('You are now logged in as ' + email, 'success')
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
            return redirect(url_for('map'))
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


def dbTrashChoices():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor'] 
    cursor.execute("select trash from d.trash_type")
    data = cursor.fetchall()
    choices = []
    for row in data:
        choices.append((row[0], row[0]))
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    return choices 





class addPointForm(Form):
    lat = FloatField('Latitude', [validators.DataRequired()])
    lon = FloatField('longitude', [validators.DataRequired()])
    choices = dbTrashChoices()
    trashType= sf(choices[0],choices=choices)

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
        
def fkTrashType(trashType):
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor'] 
    cursor.execute("select id from d.trash_type where trash = %s",[trashType])
    fk_trash_type = cursor.fetchall() 
    for row in fk_trash_type:
        fk_trash_type = row[0]
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    return  fk_trash_type   
        
    
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

"""
def allowed_file(filename):
        for i in ALLOWED_EXTENSIONS:
            if file.filename.split(".")[1] in i:
                
                print 1
                return filename
        else    
        elif    
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS
"""
def imageUpload():
    # check if the post request has the file part
   #if 'file' not  in request.files:
        #return redirect(request.url)
    if 'file' in request.files:
        #return redirect(request.url)
        file = request.files['file']
    else:
        file.filename = ''
        return file.filename   
        
    if file.filename.split(".")[1] in ALLOWED_EXTENSIONS:
        print 1
          
    #if file and (file.filename.split(".")[1] == "jpeg" or file.filename.split(".")[1] == "jpg"):
        filename = secure_filename(file.filename)
        file.filename = filename.split('.')[0] + '_' + str(uuid.uuid4()) + '.' + filename.split('.')[1]
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
        return file.filename
    
    elif file.filename  is None or file.filename  == '':
        file.filename = ''
        return file.filename
        
    elif file.filename.split(".")[1] not in ALLOWED_EXTENSIONS:
        print 0
        #file.filename = ''
        flash('ERROR! Please upload only jpeg, png, gif or tif.', 'danger')

        #return file.filename
        #elif  file and (file.filename.split(".")[1] != "jpeg" or file.filename.split(".")[1] != "jpg"):
        form = addPointForm(request.form)
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
        conn=d_conn['conn']
        conn.rollback()
        d_conn = pg_operations2.pg_disconnect2(d_conn)

        flash('ERROR! Please uplod only jpeg, png, gif or tif.', 'danger')
        return render_template('registerTrashReporter..html', form = form) 
    
    
                    
    


def paramsInsert(lat, lon, trashType, filename, address, fk_trash_type):
    params = {
                        '_lat': lat,      
                        '_lon' : lon,
                        '_cp_file_name': filename,
                        '_address': address,
                        '_fk_trash_type' :fk_trash_type 
                    }
     
    return params

def queryInsert():
    query = """insert into d.point
                    (latitude, longitude, geom, cp_file_name, address, fk_trash_type ) 
                     values (%(_lat)s,%(_lon)s,
                     ST_SetSRID(ST_MakePoint(%(_lat)s, %(_lon)s), 4326) 
                     , %(_cp_file_name)s, %(_address)s, %(_fk_trash_type)s)""" 
                     
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
                    filename = imageUpload()
 
                    print filename
                    lat = form.lat.data
                    lon = form.lon.data
                    checkPol(lat, lon, form)
                    trashType= form.trashType.data
                    fk_trash_type = fkTrashType(trashType)
                    address = nominatim(str(lat), str(lon))     
                    params = paramsInsert(lat, lon, trashType, filename, address, fk_trash_type)
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
            return render_template('registerTrashReporter..html', form = form)                            
        return render_template('registerTrashReporter..html', form = form)
    

@app.route('/removePoint', methods=['GET', 'POST'])
@is_municipality
def removePoint():
        return render_template("mapTrashReporterRemove.html")



@app.route('/stats')
@is_logged_in
def stats():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    cursor=d_conn['cursor']  
    cons="select COUNT(gid),  timestamp without time zone 'epoch' + max(extract(epoch from trash_time)) * interval '1 second', timestamp without time zone 'epoch' + min(extract(epoch from trash_time)) * interval '1 second' from d.point"
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
    fmt = '%Y-%m-%d %H:%M:%S'
    minTime = datetime.strptime(minTime, fmt)
    timeDiff = str(maxTime - minTime)
    #lista = [counter, maxTime,minTime] 
    lista = []
    lista2 = []
    dict ={}   
    cons='select trash_type, count(trash_type) from d.point group by trash_type order by trash_type;'    
    cursor.execute(cons)
    for i in cursor.fetchall():
        trashType = i[0]
        trashCounter = i[1]  
        lista2.append(trashType) 
        lista2.append(trashCounter)  
 
    meas = {"counter": counter, "maxTime": maxTime, "minTime":minTime, "timeDiff":timeDiff,
             "lista2":lista2}
    lista.append(meas)
    dict["data"]=lista
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return jsonify(dict)


@app.route('/statistics')
@is_logged_in
def statistics():
    return render_template("statsTrashReporter.html")


@app.route('/interactive/')
def interactive():
        lista = []
        dict = {}
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
        conn=d_conn['conn']
        cursor=d_conn['cursor']
    
        data = cursor.execute("SELECT  gid, st_astext(geom), address FROM d.point")
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
        cursor.execute("SELECT longitude, latitude, address FROM d.point")
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

@app.route('/background_process')
def background_process():
    try:
        lang = request.args.get('proglang', 0, type=str)
        
        return jsonify(result=lang )
    except Exception as e:
        return str(e)


@app.route('/deleteRowSim/<gid>', methods=('GET', 'POST',))
def deleteRowSim(gid):
    
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    cursor.execute("DELETE FROM d.point WHERE gid = %s",[gid])
    conn.commit()
    data = interactive2()
    d_conn = pg_operations2.pg_disconnect2(d_conn)

    return data


if __name__ == '__main__':
    app.run()
