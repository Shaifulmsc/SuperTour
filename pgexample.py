'''
Created on 28 de feb. de 2018

@author: desweb
'''
# 1.system libraries
import os, sys
import requests
# 2.second part libraries
import psycopg2 
from flask import Flask,render_template, flash, request, url_for, redirect, session, jsonify
from wtforms import Form, validators, StringField, PasswordField, RadioField,SelectField as sf, IntegerField, DecimalField, FileField
from wtforms.validators import DataRequired, Length, EqualTo, Email
from passlib.hash import sha256_crypt
from flask_security import Security, login_required, SQLAlchemySessionUserDatastore
from functools import wraps
from flask_mail import Mail, Message
#from reportlab.pdfbase.pdfform import SelectField
from werkzeug.utils import secure_filename
from flask import send_from_directory
from flask_wtf.file import FileField, FileRequired
from os.path import join, dirname, realpath
from pyupv.pg_operations2 import pg_operations2 as pgo2
from pyupv.upvgml import upvgml
from xml.etree.ElementTree import ElementTree as et
from flask.json import jsonify
from math import sqrt
import json


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

UPLOAD_FOLDER = join(dirname(realpath(__file__)), 'uploads')
#UPLOAD_FOLDER = '/uploads'
ALLOWED_EXTENSIONS = set(['gml', 'txt'])

app = Flask(__name__)
app.config.update(
    DEBUG=True,    # REMEMBER TO PUT IT AS FALSE WHEN LIVE
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
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# additional configs:
app.config['SECURITY_PASSWORD_HASH'] = 'sha256_crypt'
app.config['SECURITY_PASSWORD_SALT'] = 'fhasdgihwntlgy8f'
app.config['SECURITY_RECOVERABLE'] = True
app.debug = True



def visitor_counter(d_conn):
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    counter = 1
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    cons='select * from d.visit_num'
    cursor.execute(cons)
    lista = cursor.fetchall()
    for i in lista:
        #print i[1]
        updateCounter = i[1] + counter
        cons2='update d.visit_num set visit_num = ' + str(updateCounter)
        cursor.execute(cons2)
    conn.commit()
    #cursor.Close()
    r = cursor.rowcount    
    d_conn = pg_operations2.pg_disconnect2(d_conn)

    return r



"""
def create_user(d_conn, email, password, profession):
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    cons='insert into d.user (email, encrypted_password, profession) values ({0}), ({1}), ({2}))'.format(email, password, profession)
    cursor.execute(cons)
    conn.commit()
    returning=cursor.fetchall()
    #cursor.close()
    return returning
"""


@app.route('/')
def index():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    visitor_counter(d_conn)
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    return render_template("main.html")


@app.route('/stats')
def stats():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)

    #import sys;sys.path.append(r'/opt/liclipse/plugins/org.python.pydev_4.5.5.201603221237/pysrc')
    #import pydevd;pydevd.settrace()
    cursor=d_conn['cursor']
    cons='select visit_num from d.visit_num'
    cursor.execute(cons)
    lista = cursor.fetchall()
    cons2 = 'select count(gid) from d.user'
    cursor.execute(cons2)
    lista2 = cursor.fetchall()
    cons3 = 'select count(gid) from d.similarity'
    cursor.execute(cons3)
    lista3 = cursor.fetchall()
    cons4 = 'select count(gid) from d.accuracy'
    cursor.execute(cons4)
    lista4 = cursor.fetchall()
    d_conn = pg_operations2.pg_disconnect2(d_conn)

    #cursor.close()
    return render_template("stats.html", lista=lista, lista2=lista2, lista3=lista3, lista4=lista4)


@app.route('/map')
def map():
    testPol()
    return render_template("map.html")

class RegistrationForm(Form):
    email = StringField('Email Address', [validators.Length(min=6, max=50),validators.DataRequired()])
    password = PasswordField('New Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords must match'), validators.Length(min=6, max=50)
    ])
    confirm = PasswordField('Repeat Password')
    """
    profession = RadioField(
        'Your Profession',
        choices=[('Registrador','Registrador'), ('Notario','Notario'), ('Ing. tecnico topografo','Ing. tecnico topografo',),
        ('Ing. en geodesia','Ing. en geodesia'), ('Ing. en geomatica','Ing. en geomatica'), 
        ('Master en geomatica y geoinformacion','Master en geomatica y geoinformacion'),
        ('Arquitecto','Arquitecto'),
        ('Ing. Caminos','Ing. Caminos'),
        ('Ing. agronomo','Ing. agronomo'),
        ('Ing. Agricola','Ing. Agricola'), ('Otro','Otro')]
    """

    choices = [('Registrador','Registrador'), ('Notario','Notario'), ('Ing. tecnico topografo','Ing. tecnico topografo',),
      ('Ing. en geodesia','Ing. en geodesia'), ('Ing. en geomatica','Ing. en geomatica'), 
      ('Master en geomatica y geoinformacion','Master en geomatica y geoinformacion'),
       ('Arquitecto','Arquitecto'),
      ('Ing. Caminos','Ing. Caminos'),
       ('Ing. agronomo','Ing. agronomo'),
       ('Ing. Agricola','Ing. Agricola'), ('Otro','Otro')]
    
    profession = sf(u'Registrador',choices=choices)



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
                profession = form.profession.data
                #d_conn = pg_operations2.pg_connect2(database, user, password, host, port)

                cursor=d_conn['cursor']
                params = {
                    '_email' : email,
                    '_password' : passwordUser,
                    '_profession' : profession
                }
                query = """insert into d.user (email, encrypted_password, profession) 
                 values (%(_email)s, %(_password)s, %(_profession)s)"""
                cursor.execute(query, params)
                conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)

                #cursor.fetchall()                  
                flash('Thanks for registering!', 'success')
                return redirect(url_for('login'))
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
            session['logged_in'] = True
            session['email'] = request.form['email']
            #getEmail = cursor.execute("SELECT email FROM d.user WHERE email = %s",[email])
            #getEmail = cursor.fetchone()[0]
            #emailSplit =  session['email'].split("@")[0]
            flash('You are now logged in', 'success')
            d_conn = pg_operations2.pg_disconnect2(d_conn)

            return redirect(url_for('profile', email = session['email']))
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




# Logout
@app.route('/logout/')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

   

@app.route('/profile/<email>')
@is_logged_in
def profile(email):
    
    email = session['email']
    #emailSplit =  email.split("@")[0]
    #userEmail = emailSplit
    
    return render_template('profile.html', email=email)




@app.route("/result", methods=["POST"])
def result():
    return render_template('profile.html')    




@app.route('/interactive/')
def interactive():
    lista = []
    dict = {}
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    email = session['email']
    
    #data = cursor.execute("SELECT date,ref_cat, municipality_name, original_src FROM d.accuracy WHERE user_gid = %s",[test])
    data = cursor.execute("SELECT b.date,b.ref_cat, b.municiplity_name, b.original_src, b.deleted FROM d.similarity AS b INNER JOIN d.user AS a ON a.gid = b.user_gid WHERE a.email= %s",[email])
    #data = cursor.execute("SELECT date,ref_cat, municiplity_name, original_src FROM d.similarity WHERE user_gid = 2")

    data = cursor.fetchall()
    
    for row in data:
        if row[4] is False:    
            date = row[0]
            ref_cat = row[1]
            muni = row[2]
            crs = row[3]
            meas = {"Fecha": date, "ReferenciaCadastral": ref_cat, "Municipalidad": muni, "SRC":crs}
            lista.append(meas)
            dict["data"]=lista
    d_conn = pg_operations2.pg_disconnect2(d_conn)
    
    return jsonify(dict)
    
@app.route('/interactive2/')
def interactive2():
    lista = []
    dict = {}
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    email = session['email']

    #data = cursor.execute("SELECT date,ref_cat, municipality_name, original_src FROM d.accuracy WHERE user_gid = %s",[test])
    data = cursor.execute("SELECT  b.gid, b.date,b.ref_cat, b.municiplity_name, b.original_src, b.deleted FROM d.similarity AS b INNER JOIN d.user AS a ON a.gid = b.user_gid WHERE a.email= %s",[email])

    #data = cursor.execute("SELECT b.gid, b.date,b.ref_cat, b.municipality_name, b.original_src, b.deleted FROM d.accuracy AS b INNER JOIN d.user AS a ON a.gid = b.user_gid WHERE a.email= %s",[email])
    #data = cursor.execute("SELECT date,ref_cat, municiplity_name, original_src FROM d.similarity WHERE user_gid = 2")

    data = cursor.fetchall()
    
    for row in data:
        if row[5] is False: 
            gid = row[0] 
            date = row[1]
            ref_cat = row[2]
            muni = row[3]
            crs = row[4]
            meas = {"gid": gid, "Fecha": date, "ReferenciaCadastral": ref_cat, "Municipalidad": muni, "SRC":crs}
            lista.append(meas)
            dict["data"]=lista
            d_conn = pg_operations2.pg_disconnect2(d_conn)
        return jsonify(dict)

@app.route('/deleteRowSim/<gid>', methods=('GET', 'POST',))
def deleteRowSim(gid):
    
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    cursor=d_conn['cursor']
    #data = cursor.execute("SELECT b.date,b.ref_cat, b.municipality_name, b.original_src, b.deleted FROM d.accuracy AS b INNER JOIN d.user AS a ON a.gid = b.user_gid WHERE a.email= %s",[email])
    #cursor.execute("UPDATE d.accuracy AS a set deleted = True FROM d.user as b where b.gid = a.user_gid and b.email = %s",[gid])
    test = cursor.execute("UPDATE d.similarity set deleted = True where gid = %s",[gid])
    conn.commit()
    d_conn = pg_operations2.pg_disconnect2(d_conn)

    return 123
    


@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/help')
def help():
    return render_template('help.html')



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
        data = cursor.execute("SELECT encrypted_password FROM d.user WHERE email = %s",[email])
        data = cursor.fetchone()[0]
        d_conn = pg_operations2.pg_disconnect2(d_conn)

        if data:
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
        print password_reset_serializer
        email = password_reset_serializer.loads(token, salt='password-reset-salt', max_age=3600)
        print email

        if form.validate():
            if 1==1:
                print 1
                
                password2 = sha256_crypt.encrypt(form.password.data)
                print password2
                print d_conn
                
                print conn
                cursor=d_conn['cursor']
                print cursor
                print 2
                #cursor.execute("UPDATE d.user set encrypted_password = '{0}' WHERE  email = '{1}';".format(password,email))
                cursor.execute("UPDATE d.user set encrypted_password = %s WHERE  email = %s;",[password2,email])
                #cons2 = "UPDATE d.user set encrypted_password=(%s) WHERE email = (%s)", (password,email,)
                #cons3 = "UPDATE d.user set encrypted_password=(%s) WHERE email = (%s)", (password,[email])
                #cons2='update d.user set encrypted_password = ' + password + 'where email = ' + [email]
                #print cons2
                #print cons3
                #cursor.execute(cons3)
                #cursor.execute(cons3)
                conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)
    
                flash('Your password has been updated!', 'success')
                return redirect(url_for('login'))

        return render_template('emailForgotPassToken.html', form=form, token=token)

    except:
        flash('The password reset link is invalid or has expired.', 'error')
        return redirect(url_for('login'))
    
from datetime import datetime

   

class similarityForm(Form):
    src = StringField('SRC', [validators.DataRequired()])
    ref_cat = StringField('La referencia cadastral', [validators.DataRequired(), validators.Length(min=14, max=14)])
    cp_accuracy = DecimalField('Error de precision del area original', [validators.DataRequired()])
    municipio = StringField('Municipio')
    lru = FileField('Carga GML de tu trabajo', validators=[FileRequired()])
    idvfir = StringField('identificador de cadaster')
    lru_accuracy = DecimalField('Error de precision de tu trabajo', [validators.DataRequired()])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/similarity', methods=['GET', 'POST'])
@is_logged_in
def upload_file():

        form = similarityForm(request.form)
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
        conn=d_conn['conn']
        cursor=d_conn['cursor']  
        email = session['email']
        
        if request.method == 'POST':
   
            # check if the post request has the file part
            if 'file' not in request.files:
                print 'no file'
                return redirect(request.url)
            file = request.files['file']
            # if user does not select file, browser also
            # submit a empty part without filename
            if file.filename == '':
                print 'no filename'
                return redirect(request.url)
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                 
            #if form.validate():                 
                src = form.src.data
                ref_cat = form.ref_cat.data
                #test = something(ref_cat)
                cp_accuracy = form.cp_accuracy.data
                municipio = form.municipio.data
                lru = form.ref_cat.data
                dt = datetime.now() 
                idvfir = form.idvfir.data
                lru_accuracy = form.lru_accuracy.data
                
                #cursor.execute("SELECT b.user_gid FROM d.similarity AS b INNER JOIN d.user AS a ON a.gid = b.user_gid WHERE a.email= %s",[email])
                cursor.execute("SELECT gid FROM d.user WHERE email= %s",[email])

                user_gid= cursor.fetchone()[0]
                params = {
                    '_user_gid': user_gid,      
                    '_original_src' : src,
                    '_ref_cat' : ref_cat,
                    '_cp_accuracy' : cp_accuracy,

                    '_municiplity_name' :municipio,
                    '_cp_file_name': filename,
                    '_lru_accuracy': lru_accuracy,
                    '_time': dt,
                }
                query = """insert into d.similarity
                (user_gid, original_src, ref_cat, cp_accuracy,municiplity_name, cp_file_name, deleted,lru_accuracy , date) 
                 values (%(_user_gid)s, %(_original_src)s, %(_ref_cat)s,%(_cp_accuracy)s, %(_municiplity_name)s,
                 %(_cp_file_name)s, False, %(_lru_accuracy)s, %(_time)s)"""   
                cursor.execute(query, params)
                conn.commit()
                
              
                
                
                q = cursor.execute("SELECT b.gid, b.ref_cat FROM d.similarity AS b INNER JOIN d.user AS a ON a.gid = b.user_gid WHERE a.email= %s ORDER BY b.gid DESC LIMIT 1",[email])

                q = cursor.fetchall()
        
                data = {'ref_cat':q}
                data = jsonify(data)
                d_conn = pg_operations2.pg_disconnect2(d_conn)                    
                flash('Similitud uploaded', 'success')
                testPol()
                return redirect(url_for('map',ref_cat= ref_cat))
                return redirect(url_for('uploaded_file',
                                        filename=filename)) 
        return render_template('similarity.html', form = form)
            
        return '''
        <!doctype html>
        <title>Upload new File</title>
        <h1>Yair</h1>
        <form action="" method=post enctype=multipart/form-data>
          <input type=file name=file>
    
          <input type=submit value=Upload>
        </form>
        '''
    
@app.route('/something/', methods=['post'])
def something():
    form = similarityForm(request.form)
    ref_cat = form.ref_cat.data
    entry2Value = request.args.get(ref_cat)
    
    return jsonify({'ref_cat': ref_cat})

@app.route('/background_process')
def background_process():
    try:
        lang = request.args.get('proglang', 0, type=str)
        if lang.lower() == 'python':
            form = similarityForm(request.form)
            ref_cat = form.ref_cat.data
            return jsonify(result=ref_cat)
        else:
            return jsonify(result='Try again.')
    except Exception as e:
        return str(e)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
filename)

"""
@app.route('/bobo', methods=['GET', 'POST'])
@is_logged_in
def similarity():
    d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
    conn=d_conn['conn']
    form = similarityForm(request.form)
    try:
        if request.method == 'POST' and form.validate():
            if 1==1:  
                 
                src = form.src.data
                print src
                ref_cat = form.ref_cat.data
                cp_accuracy = form.ref_cat.data
                municipio = form.ref_cat.data
                lru = form.ref_cat.data
                #print lru
                #test =upload_file(lru)
                #print test
                idvfir = form.ref_cat.data
                lru_accuracy = form.ref_cat.data
                #cursor=d_conn['cursor']
                #cursor.execute()
                #conn.commit()
                d_conn = pg_operations2.pg_disconnect2(d_conn)
                flash('Similitud uploaded', 'success')
                return redirect(url_for('map'))
        return render_template('similarity.html', form=form)
    except:
        conn=d_conn['conn']
        conn.rollback()
        d_conn = pg_operations2.pg_disconnect2(d_conn)

        return render_template('similarity.html', form=form)

"""

   
@app.route('/get_gml/', methods=['GET'])    
def get_gml():
    if request.method == 'GET':
        #retrieves the refcat or ''
        #3662001TF3136S
        refcat=request.args.get('refcat', '')
        print refcat
        if refcat=='':
            #if gid is '' means that it was not sent. The call was: http://localhost:5000/map/
            resp_json=json.dumps({"ok":'false', 'data':'', 'message':'You have to specify a refcat'})
            return resp_json
        labelInit= '<gml:posList srsDimension="2"'
        labelFin= '</gml:posList>'
        gml = requests.get('http://ovc.catastro.meh.es/INSPIRE/wfsCP.aspx?service=wfs&version=2&request=getfeature&STOREDQUERIE_ID=GetParcel&refcat='+refcat+'&srsname=EPSG::4258').content
        boundingBox=upvgml.extractFieldValueFromGml(gml,labelInit,labelFin)
        #reverse=pg_operations2.reverseXY(coords_geom=boundingBox,separatorIn=' ',separatorOut=' ')
        resp_answer=pg_operations2.transform_coords_ol_to_postgis(coords_geom=reverse, splitString=' ')
        dict = {}
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
        conn=d_conn['conn']
        cursor=d_conn['cursor']
        coords="'POLYGON(({resp_answer}))'".format(resp_answer=resp_answer)
        data = 'SELECT ST_ASGEOJSON(ST_GEOMETRYFROMTEXT({coords},4258));'.format(coords=coords)
        cursor.execute(data)
        lista = cursor.fetchall()
        r=lista[0][0]
        print r
        d_conn = pg_operations2.pg_disconnect2(d_conn)
        return r

gmalTest = """
<?xml version="1.0" encoding="ISO-8859-1"?>

<!--Parcela Catastral de la D.G. del Catastro.-->

<!--La precision es la que corresponde nominalmente a la escala de captura de la cartografia-->

<FeatureCollection xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:cp="http://inspire.ec.europa.eu/schemas/cp/4.0" xmlns:gmd="http://www.isotc211.org/2005/gmd" xsi:schemaLocation="http://www.opengis.net/wfs/2.0 http://schemas.opengis.net/wfs/2.0/wfs.xsd http://inspire.ec.europa.eu/schemas/cp/4.0 http://inspire.ec.europa.eu/schemas/cp/4.0/CadastralParcels.xsd" xmlns="http://www.opengis.net/wfs/2.0" timeStamp="2018-04-01T02:08:45" numberMatched="1" numberReturned="1">

  <member>

    <cp:CadastralParcel gml:id="ES.SDGC.CP.3662001TF3136S">

      <cp:areaValue uom="m2">930</cp:areaValue>

      <cp:beginLifespanVersion>2005-08-16T00:00:00</cp:beginLifespanVersion>

      <cp:endLifespanVersion xsi:nil="true" nilReason="http://inspire.ec.europa.eu/codelist/VoidReasonValue/Unpopulated"></cp:endLifespanVersion>

      <cp:geometry>

        <gml:MultiSurface gml:id="MultiSurface_ES.SDGC.CP.3662001TF3136S" srsName="http://www.opengis.net/def/crs/EPSG/0/4258">

          <gml:surfaceMember>

            <gml:Surface gml:id="Surface_ES.SDGC.CP.3662001TF3136S.1" srsName="http://www.opengis.net/def/crs/EPSG/0/4258">

              <gml:patches>

                <gml:PolygonPatch>

                <gml:exterior>

                    <gml:LinearRing>

                      <gml:posList srsDimension="2" count="16">36.252591 -5.965154 36.252575 -5.96518 36.252553 -5.965232 36.252539 -5.965287 36.252532 -5.965345 36.252534 -5.965404 36.252546 -5.965465 36.252563 -5.965515 36.252523 -5.965584 36.252385 -5.965661 36.252504 -5.965644 36.252789 -5.965526 36.252827 -5.965434 36.252746 -5.965299 36.252634 -5.965168 36.252591 -5.965154</gml:posList>

                    </gml:LinearRing>

                </gml:exterior>

                </gml:PolygonPatch>

              </gml:patches>

            </gml:Surface>

          </gml:surfaceMember>

        </gml:MultiSurface>

      </cp:geometry>

      <cp:inspireId>

        <Identifier xmlns="http://inspire.ec.europa.eu/schemas/base/3.3">

          <localId>3662001TF3136S</localId>

          <namespace>ES.SDGC.CP</namespace>

        </Identifier>

      </cp:inspireId>

      <cp:label>01</cp:label>

      <cp:nationalCadastralReference>3662001TF3136S</cp:nationalCadastralReference>

      <cp:referencePoint>

        <gml:Point gml:id="ReferencePoint_ES.SDGC.CP.3662001TF3136S" srsName="http://www.opengis.net/def/crs/EPSG/0/4258"> 

          <gml:pos>36.252645 -5.965413</gml:pos>

        </gml:Point>

      </cp:referencePoint>

    </cp:CadastralParcel>

  </member>

</FeatureCollection>
    """
    
@app.route('/testPol/', methods=('GET', 'POST'))
def testPol():
    if request.method == "POST":
        d_conn = pg_operations2.pg_connect2(database, user, password, host, port)
        conn=d_conn['conn']
        cursor=d_conn['cursor']
        email = session['email']
        cadastralGML = request.get_data()
        cadastralGML = gmalTest
        print cadastralGML
        #dbUL = pgo2.transform_coords_land_registry_gml_to_postgis(cooLR)
        #cooUL=upvgml.extractFieldValueFromGml(ul,'<gml:posList srsDimension="2"','</gml:posList>')
        cooCP=upvgml.extractFieldValueFromGml(cadastralGML,'<gml:posList srsDimension="2"','</gml:posList>')
        print cooCP
        #dbCP =  pgo2.transform_coords_land_registry_gml_to_postgis(cooUL)
        dbCP =  pgo2.transform_coords_ol_to_postgis(coords_geom=cooCP, splitString=' ')
              
        #cursor.execute("SELECT b.user_gid FROM d.similarity AS b INNER JOIN d.user AS a ON a.gid = b.user_gid WHERE a.email= %s",[email])
        cursor.execute("SELECT gid FROM d.user WHERE email= %s",[email])

        user_gid= cursor.fetchone()[0]
        cursor.execute("SELECT b.gid FROM d.similarity AS b left JOIN d.cp AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        similarity_gid= cursor.fetchone()[0]
        params = {
            '_similarity_gid': similarity_gid
        }
            

        #values (%(_similarity_gid)s, (SELECT ST_Multi(ST_GeomFromText('POLYGON((""" + dbCP + """))',4258))))"""   
 
                
        querySim = """insert into d.cp
        (similarity_gid, geom_multypolygon) 
         values (%(_similarity_gid)s, (SELECT ST_Multi(ST_GeomFromText('POLYGON((36.252591 -5.965154,36.252575 -5.96518,36.252553 -5.965232,36.252539 -5.965287,36.252532 -5.965345,36.252534 -5.965404,36.252546 -5.965465,36.252563 -5.965515,36.252523 -5.965584,36.252385 -5.965661,36.252504 -5.965644,36.252789 -5.965526,36.252827 -5.965434,36.252746 -5.965299,36.252634 -5.965168,36.252591 -5.965154))',4258))))"""   
        

        cursor.execute(querySim, params)
        conn.commit()
        print 'done CP'
        #ul = request.get_data()


        #cooLR= upvgml.extractFieldValueFromGml(ul,'<gml:coordinates>','</gml:coordinates>')
        #dbUL = pgo2.transform_coords_land_registry_gml_to_postgis(cooLR)

        cursor.execute("SELECT b.gid FROM d.similarity AS b left JOIN d.lru AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        similarity_gid= cursor.fetchone()[0]
        print 'this is the similarity_gid',  similarity_gid
        params = {
            '_similarity_gid': similarity_gid
        }
            
        #values (%(_similarity_gid)s, (SELECT ST_Multi(ST_GeomFromText('POLYGON((""" + dbUL + """))',4258))))"""   

                
        querySim = """insert into d.lru
        (similarity_gid, geom_multypolygon) 
         values (%(_similarity_gid)s, (SELECT ST_Multi(ST_GeomFromText('POLYGON((-0.323883 39.533364,-0.324142 39.533497,-0.324115 39.533533,-0.323828 39.533909,-0.323346 39.533644,-0.323324 39.533632,-0.323634 39.533232,-0.323654 39.533243,-0.323883 39.533364))',4258))))"""   
        

        cursor.execute(querySim, params)
        conn.commit()
        
        cursor.execute("SELECT st_area(a.geom_multypolygon) FROM d.similarity AS b left JOIN d.cp AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        acp = cursor.fetchone()[0]
        cursor.execute("SELECT st_area(a.geom_multypolygon) FROM d.similarity AS b left JOIN d.lru AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        alru = cursor.fetchone()[0]
        cursor.execute("select st_area(st_intersection(a.geom_multypolygon, b.geom_multypolygon)) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s   order by a.similarity_gid desc limit 1",[user_gid])
        ai = cursor.fetchone()[0]
        similarity = round((ai * 2)/(acp + alru) * 10)
        
        cursor.execute("SELECT a.geom_multypolygon FROM d.similarity AS b left JOIN d.cp AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        cpGeom = cursor.fetchone()[0]
        cursor.execute("SELECT a.geom_multypolygon FROM d.similarity AS b left JOIN d.lru AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        lruGeom = cursor.fetchone()[0]
        cursor.execute("SELECT b.cp_accuracy FROM d.similarity AS b left JOIN d.cp AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        cp_error= cursor.fetchone()[0]
        cursor.execute("SELECT b.lru_accuracy FROM d.similarity AS b left JOIN d.cp AS a ON a.similarity_gid = b.gid WHERE b.user_gid= %s order by b.gid desc limit 1",[user_gid])
        lru_error= cursor.fetchone()[0]
        cursor.callproc('script.error_area_multipoligono', (cpGeom,cp_error))
        cp_area_error = cursor.fetchone()[0]
        cursor.callproc('script.error_area_multipoligono', (cpGeom,lru_error))
        lru_area_error = cursor.fetchone()[0]
        
        cursor.execute("select st_area(a.geom_multypolygon) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s  AND  ST_Within(a.geom_multypolygon, b.geom_multypolygon) = false order by a.similarity_gid desc limit 1",[user_gid])
        acp_not_within_lru = cursor.fetchone()[0]
        #if rows_count == 0 or rows_count is None:
            #acp_not_within_lru = 0.0
        #else:
            #acp_not_within_lru = rows_count.fetchone()[0]
        
        
        cursor.execute("select st_area(a.geom_multypolygon) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s  AND  ST_Contains(a.geom_multypolygon, b.geom_multypolygon) = false order by a.similarity_gid desc limit 1",[user_gid])
        alru_not_in_cp = cursor.fetchone()[0]
        #if rows_count_con == 0 or rows_count_con is None:
            #alru_not_in_cp = 0.0
        #else:
            #alru_not_in_cp = rows_count_con.fetchone()[0]
        
        cursor.execute("select st_x(st_centroid(a.geom_multypolygon)) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s   order by a.similarity_gid desc limit 1",[user_gid])
        xcp = cursor.fetchone()[0]
        cursor.execute("select st_x(st_centroid(b.geom_multypolygon)) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s   order by a.similarity_gid desc limit 1",[user_gid])
        xlru = cursor.fetchone()[0]
        
        cursor.execute("select st_y(st_centroid(a.geom_multypolygon)) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s   order by a.similarity_gid desc limit 1",[user_gid])
        ycp = cursor.fetchone()[0]
        cursor.execute("select st_y(st_centroid(b.geom_multypolygon)) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s   order by a.similarity_gid desc limit 1",[user_gid])
        ylru = cursor.fetchone()[0]
        
        ay = ycp - ylru
        ax = xcp - xlru

        d_geoc = sqrt((xcp - xlru)**2 + (ycp - ylru)**2)
        
        cursor.execute("select st_perimeter(b.geom_multypolygon) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s   order by a.similarity_gid desc limit 1",[user_gid])
        lru_perimeter = cursor.fetchone()[0]
        cursor.execute("select st_perimeter(a.geom_multypolygon) from d.cp as a INNER JOIN d.lru as b on a.similarity_gid = b.similarity_gid   inner join d.similarity as c on c.gid=b.similarity_gid  WHERE c.user_gid= %s   order by a.similarity_gid desc limit 1",[user_gid])
        cp_perimeter = cursor.fetchone()[0]
        dif_perimeter = cp_perimeter - lru_perimeter
        
        cursor.execute("SELECT original_src,ref_cat,cp_accuracy,lru_accuracy  FROM d.similarity   WHERE user_gid= %s   order by gid desc limit 1",[user_gid])
        simDetails = cursor.fetchone()
        original_src = simDetails[0]
        ref_cat = simDetails[1]
        cp_accuracy = simDetails[2]
        lru_accuracy = simDetails[3]
        
        print  lru_accuracy
        #print simDetails
        print dif_perimeter
        print lru_perimeter
        print d_geoc
        print ay
        print ax
        print alru_not_in_cp
        print acp_not_within_lru
        print abs(cp_area_error-lru_area_error)
        print lru_area_error
        print  cp_area_error
        print 123
        print lruGeom
        print cpGeom
        print similarity
        print ai
        print acp
        print alru
        
        a_difference = abs(acp - alru) 
        resultsList = []
        resultDict = {}
        resultsList.append(acp)
        resultDict['CP_area'] = [acp]
        resultDict['LRU_area'] = [alru]
        resultDict['Interseccion_area'] = [ai]
        resultDict['SIMILARITY'] = [similarity]
        resultDict['cp_area_error'] = [cp_area_error]
        resultDict['lru_area_error'] = [lru_area_error]
        resultDict['diferencia_area'] = [a_difference]
        resultDict['CP_fuera_lru'] = [acp_not_within_lru]
        resultDict['lru_fuera_cp'] = [alru_not_in_cp]
        resultDict['x_centroid_diferencia'] = [ax]
        resultDict['y_centroid_diferencia'] = [ay]
        resultDict['distancia_centroids'] = [d_geoc]
        resultDict['lru_perimetro'] = [lru_perimeter]
        resultDict['diferencia_perimetro'] = [dif_perimeter]
        resultDict['cadastral_reference'] = [ref_cat]
        resultDict['CP_accuracy'] = [cp_accuracy]
        resultDict['lru_accuracy'] = [lru_accuracy]
        resultDict['original_SRC'] = [original_src]
        
        params = {
                    '_similarity': similarity, 
                    'similarity_gid': similarity_gid,     
                    '_cp_area_error' : cp_area_error,
                    '_acp' : acp,
                    '_intersection_area' : ai,
                    '_alru' :alru,
                    '_acp_not_int_lru': acp_not_within_lru,
                    '_alru_not_in_cp': alru_not_in_cp,
                    '_ax': ax,
                    '_ay': ay,
                    '_d_geoc': d_geoc,
                    '_a_difference': a_difference,
                    '_cp_perimeter': cp_perimeter,
                    '_lru_perimeter': lru_perimeter,
                    '_dif_parameter': dif_perimeter
                }
        query = """insert into d.similarity_result
        (similarity,similarity_gid, cp_area_error, 
        acp, intersection_area,alru,
         acp_not_int_lru, alru_not_in_cp,
         ax , ay, d_geoc, a_difference,cp_perimeter,
         lru_perimeter, dif_parameter) 
         values (%(_similarity)s,%(similarity_gid)s,
          %(_cp_area_error)s,
          %(_acp)s,%(_intersection_area)s,
           %(_alru)s,
         %(_acp_not_int_lru)s, %(_alru_not_in_cp)s,
         %(_ax)s,%(_ay)s,
          %(_d_geoc)s,%(_a_difference)s,%(_cp_perimeter)s,
          %(_lru_perimeter)s,
           %(_dif_parameter)s)"""   
        cursor.execute(query, params)
        conn.commit()
        d_conn = pg_operations2.pg_disconnect2(d_conn)

        print resultDict

        return jsonify(resultsList)
        #print pgo2.transform_coords_ol_to_postgis(coords_geom=cooCP, splitString=' ')
        
        #cooLR=upvgml.extractFieldValueFromGml(landRegistryGML,'<gml:coordinates>','</gml:coordinates>')
        #print cooLR
        
            
        #idufir=upvgml.extractFieldValueFromGml(landRegistryGML,'<idufir>','</idufir>')
        #print idufir

@app.route('/results/', methods=('GET', 'POST'))
def simResults():
    result = testPol()
    print result
    return render_template('simResults.html', result=result)
    
if __name__ == '__main__':
   app.run()

