#!/usr/bin/env python
import cartwrap, gen2dict, geojson_extrema, awslambda, tracking, custom_captcha
import settings
import recaptcha_verify

# !!!DO NOT MODFIY THE FOLLOWING SECTION
from handlers import test
from handlers import argentina
from handlers import australia
from handlers import canada
from handlers import japan2
from handlers import france
from handlers import uae
from handlers import asean
from handlers import mexico
from handlers import singaporePA
from handlers import saudiArabia
from handlers import netherlands
from handlers import thailand
from handlers import phl
from handlers import israel3
from handlers import vietnam
from handlers import southAfrica
from handlers import italy2
from handlers import colombia
from handlers import southKorea2
from handlers import newZealand
from handlers import europe
from handlers import algeria
from handlers import libya
#from handlers import pakistan
from handlers import switzerland
from handlers import ireland
from handlers import poland
from handlers import sweden
from handlers import croatia
from handlers import czechrepublic3
from handlers import hungary
from handlers import unitedkingdom2
from handlers import finland
from handlers import austria
from handlers import denmark
from handlers import belgium
from handlers import russia
from handlers import nigeria
from handlers import luxembourg
from handlers import bangladesh
from handlers import sanMarino
from handlers import portugal
from handlers import greece
from handlers import malaysia
from handlers import qatar
from handlers import turkey
from handlers import cambodia
from handlers import andorra
from handlers import ethiopia
from handlers import myanmar
from handlers import chile
from handlers import kaz
from handlers import sudan
from handlers import mongolia
from handlers import peru
from handlers import pak
from handlers import bolivia
from handlers import iceland
from handlers import laos
from handlers import domrep
from handlers import laos
from handlers import paraguay
from handlers import nepal
from handlers import world
from handlers import angola
from handlers import romania
from handlers import ukraine
from handlers import jamaica
from handlers import yemen
from handlers import belarus
from handlers import bahamas
from handlers import guyana
from handlers import washington
from handlers import lebanon
from handlers import spain5
from handlers import arab_league
from handlers import estonia
from handlers import usa
from handlers import brazil
from handlers import china
from handlers import china2
from handlers import india
from handlers import srilanka
from handlers import germany
from handlers import indonesia
from handlers import singaporeRe
from handlers import singapore2
# ---addmap.py header marker---
# !!!END DO NOT MODFIY

import json
import csv
import codecs
import re
import io
import string
import random
import datetime
from flask import Flask, request, session, Response, flash, redirect, render_template, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
import validate_email
import smtplib
import email.mime.text
import socket
import redis

from asset import Asset

app = Flask(__name__)
CORS(app)
Asset(app)

app.secret_key = "LTTNWg8luqfWKfDxjFaeC3vYoGrC2r2f5mtXo5IE/jt1GcY7/JaSq8V/tB"
app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
# This gets rid of an annoying Flask error message. We don't need this feature anyway.
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['ENV'] = 'development' if settings.DEBUG else 'production'

# Whenever you make changes to the DB models, you must run commands as follows:
# export FLASK_APP=web.py
# flask db migrate -m "Migration log."
# flask db upgrade
if settings.USE_DATABASE:
    db = SQLAlchemy(app)
    migrate = Migrate(app, db)

redis_conn = redis.Redis(host=settings.CARTOGRAM_REDIS_HOST, port=settings.CARTOGRAM_REDIS_PORT, db=0)

cartogram_handlers = {
#'test': test.CartogramHandler(),
'argentina': argentina.CartogramHandler(),
'australia': australia.CartogramHandler(),
'canada': canada.CartogramHandler(),
'japan2': japan2.CartogramHandler(),
'france': france.CartogramHandler(),
'uae': uae.CartogramHandler(),
'asean': asean.CartogramHandler(),
'mexico': mexico.CartogramHandler(),
'singaporePA': singaporePA.CartogramHandler(),
'saudiArabia': saudiArabia.CartogramHandler(),
'netherlands': netherlands.CartogramHandler(),
'thailand': thailand.CartogramHandler(),
'phl': phl.CartogramHandler(),
'israel3': israel3.CartogramHandler(),
'vietnam': vietnam.CartogramHandler(),
'southAfrica': southAfrica.CartogramHandler(),
'italy2': italy2.CartogramHandler(),
'colombia': colombia.CartogramHandler(),
'southKorea2': southKorea2.CartogramHandler(),
'newZealand': newZealand.CartogramHandler(),
'europe': europe.CartogramHandler(),
'algeria': algeria.CartogramHandler(),
'libya': libya.CartogramHandler(),
#'pakistan': pakistan.CartogramHandler(),
'switzerland': switzerland.CartogramHandler(),
'ireland': ireland.CartogramHandler(),
'poland': poland.CartogramHandler(),
'sweden': sweden.CartogramHandler(),
'croatia': croatia.CartogramHandler(),
'czechrepublic3': czechrepublic3.CartogramHandler(),
'hungary': hungary.CartogramHandler(),
'unitedkingdom2': unitedkingdom2.CartogramHandler(),
'finland': finland.CartogramHandler(),
'austria': austria.CartogramHandler(),
'denmark': denmark.CartogramHandler(),
'belgium': belgium.CartogramHandler(),
'nigeria': nigeria.CartogramHandler(),
'russia':russia.CartogramHandler(),
'luxembourg': luxembourg.CartogramHandler(),
'bangladesh': bangladesh.CartogramHandler(),
'sanMarino': sanMarino.CartogramHandler(),
'portugal': portugal.CartogramHandler(),
'greece': greece.CartogramHandler(),
'malaysia': malaysia.CartogramHandler(),
'qatar': qatar.CartogramHandler(),
'turkey': turkey.CartogramHandler(),
'cambodia': cambodia.CartogramHandler(),
'andorra': andorra.CartogramHandler(),
'ethiopia': ethiopia.CartogramHandler(),
'myanmar': myanmar.CartogramHandler(),
'chile': chile.CartogramHandler(),
'kaz': kaz.CartogramHandler(),
'sudan': sudan.CartogramHandler(),
'mongolia': mongolia.CartogramHandler(),
'peru': peru.CartogramHandler(),
'pak': pak.CartogramHandler(),
'bolivia': bolivia.CartogramHandler(),
'iceland': iceland.CartogramHandler(),
'domrep': domrep.CartogramHandler(),
'laos': laos.CartogramHandler(),
'paraguay': paraguay.CartogramHandler(),
'nepal': nepal.CartogramHandler(),
'world': world.CartogramHandler(),
'angola': angola.CartogramHandler(),
'romania': romania.CartogramHandler(),
'ukraine': ukraine.CartogramHandler(),
'jamaica': jamaica.CartogramHandler(),
'yemen': yemen.CartogramHandler(),
'belarus': belarus.CartogramHandler(),
'bahamas': bahamas.CartogramHandler(),
'guyana': guyana.CartogramHandler(),
'washington': washington.CartogramHandler(),
'lebanon': lebanon.CartogramHandler(),
'spain5': spain5.CartogramHandler(),
'arab_league': arab_league.CartogramHandler(),
'estonia': estonia.CartogramHandler(),
'usa': usa.CartogramHandler(),
'brazil': brazil.CartogramHandler(),
'china': china.CartogramHandler(),
'china2': china2.CartogramHandler(),
'india': india.CartogramHandler(),
'srilanka': srilanka.CartogramHandler(),
'germany': germany.CartogramHandler(),
'indonesia': indonesia.CartogramHandler(),
'singaporeRe': singaporeRe.CartogramHandler(),
'singapore2': singapore2.CartogramHandler(),
# ---addmap.py body marker---
# !!!END DO NOT MODFIY
}

default_cartogram_handler = "usa"

if settings.USE_DATABASE:
    class CartogramEntry(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        string_key = db.Column(db.String(32), unique=True, nullable=False)
        date_created = db.Column(db.DateTime(), nullable=False)
        date_accessed = db.Column(db.DateTime(), server_default='0001-01-01 00:00:00')        
        handler = db.Column(db.String(100), nullable=False)
        areas_string = db.Column(db.UnicodeText(), nullable=False)
        cartogram_data = db.Column(db.UnicodeText(), nullable=False)
        cartogramui_data = db.Column(db.UnicodeText(), nullable=False)

        def __repr__(self):
            return "<CartogramEntry {}>".format(self.string_key)


# This function returns a random string containg lowercase letters and numbers that is *length* characters long.
# This is used to generate the unique string key associated with each cartogram.
def get_random_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_lowercase + string.digits) for _ in range(length))


@app.route('/consent', methods=['POST'])
def consent():
    user_consent = request.form.get("consent", "")

    if user_consent == "yes":
        resp = Response(json.dumps({'error': 'none', 'tracking_id': settings.CARTOGRAM_GA_TRACKING_ID}),
                        content_type='application/json', status=200)
        resp.set_cookie("tracking", "track", max_age=31556926)  # One year
        return resp
    else:
        resp = Response(json.dumps({'error': 'none'}), content_type='application/json', status=200)
        resp.set_cookie("tracking", "do_not_track", max_age=31556926)
        return resp


@app.route('/', methods=['GET'])
def index():
    return render_template('welcome.html', page_active='home', tracking=tracking.determine_tracking_action(request))


@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html', page_active='about', tracking=tracking.determine_tracking_action(request))


@app.route('/cookies', methods=['GET'])
def cookies():
    return render_template('cookies.html', page_active='', tracking=tracking.determine_tracking_action(request))


@app.route('/faq', methods=['GET'])
def faq():
    return render_template('faq.html', page_active='faq', tracking=tracking.determine_tracking_action(request))


@app.route('/tutorial', methods=['GET'])
def tutorial():
    return render_template('tutorial.html', page_active='tutorial',
                           tracking=tracking.determine_tracking_action(request))

@app.route('/gencaptcha', methods=['GET'])
def gencaptcha():
    captcha = custom_captcha.generate_captcha()
    session['captcha_hashed'] = captcha['captcha_hashed']

    return Response(json.dumps({'error': 'none', 'captcha_image': captcha['captcha_image'], 'captcha_audio': captcha['captcha_audio']}),
                        content_type='application/json', status=200)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'GET':
        csrf_token = get_random_string(50)
        session['csrf_token'] = csrf_token

        captcha = custom_captcha.generate_captcha()
        session['captcha_hashed'] = captcha['captcha_hashed']

        return render_template('contact.html', page_active='contact', name="", message="", email_address="", subject="",
                               csrf_token=csrf_token, tracking=tracking.determine_tracking_action(request),
                               captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])
    else:

        name = request.form.get('name', '')
        email_address = request.form.get('email', '')
        subject = request.form.get('subject', '')
        message = request.form.get('message', '')
        csrf = request.form.get('csrftoken', '')
        captcha = custom_captcha.generate_captcha()

        if 'csrf_token' not in session:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Invalid CSRF token.', 'danger')
            csrf_token = get_random_string(50)
            session['csrf_token'] = csrf_token
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        if session['csrf_token'] != csrf or len(session['csrf_token'].strip()) < 1:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Invalid CSRF token.', 'danger')
            csrf_token = get_random_string(50)
            session['csrf_token'] = csrf_token
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        csrf_token = get_random_string(50)
        session['csrf_token'] = csrf_token

        if len(name.strip()) < 1 or len(subject.strip()) < 1 or len(message.strip()) < 1:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('You must fill out all of the form fields', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        if not validate_email.validate_email(email_address):
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('You must enter a valid email address.', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        if 'captcha_hashed' not in session:
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Please retry completing the CAPTCHA.', 'danger')
            csrf_token = get_random_string(50)
            session['csrf_token'] = csrf_token
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'],
                                   captcha_audio=captcha['captcha_audio'])

        if not custom_captcha.validate_captcha(request.form.get("captcha", ""), session['captcha_hashed']):
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('Please retry completing the CAPTCHA.', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        # Escape all of the variables:
        name = name.replace("<", "&lt;")
        name = name.replace(">", "&gt;")

        subject = subject.replace("<", "&lt;")
        subject = subject.replace(">", "&gt;")

        message = message.replace("<", "&lt;")
        message = message.replace(">", "&gt;")

        # Generate the message body
        message_body = """A message was received from the go-cart.io contact form.

Name:       {}
Email:      {}
Subject:    {}

Message:

{}""".format(name, email_address, subject, message)

        mime_message = email.mime.text.MIMEText(message_body)
        mime_message['Subject'] = "go-cart.io Contact Form: " + subject
        mime_message['From'] = settings.SMTP_FROM_EMAIL
        mime_message['To'] = settings.SMTP_DESTINATION

        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as smtp:

                if settings.SMTP_AUTHENTICATION_REQUIRED:
                    smtp.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

                smtp.send_message(mime_message)

                smtp.quit()
        # For some reason connect doesn't catch the socket error
        # *sigh*
        except (smtplib.SMTPException, socket.gaierror):
            session['captcha_hashed'] = captcha['captcha_hashed']
            flash('There was an error sending your message.', 'danger')
            return render_template('contact.html', page_active='contact', name=name, message=message,
                                   email_address=email_address, subject=subject, csrf_token=csrf_token,
                                   tracking=tracking.determine_tracking_action(request),
                                   captcha_image=captcha['captcha_image'], captcha_audio=captcha['captcha_audio'])

        session['captcha_hashed'] = ""
        flash('Your message was successfully sent.', 'success')
        return redirect(url_for('contact'))


@app.route('/cartogram', methods=['GET'])
def get_cartogram():    
    return get_cartogram_by_name(default_cartogram_handler)


@app.route('/cartogram/<map_name>', methods=['GET'])
def get_cartogram_by_name(map_name):

    if map_name not in cartogram_handlers:
        return Response('Cannot find the map {}'.format(map_name), status=500)
    
    cartogram_handlers_select = {}

    for key, handler in cartogram_handlers.items():
        for selector_name in handler.selector_names():
            cartogram_handlers_select[key] = selector_name

    dict(sorted(cartogram_handlers_select.items()))

    return render_template('cartogram.html', page_active='cartogram', 
                           maps=cartogram_handlers_select,
                           map_name=map_name,
                           tracking=tracking.determine_tracking_action(request))


@app.route('/cart/<string_key>', methods=['GET'])
def cartogram_by_key(string_key):
    if not settings.USE_DATABASE:
        return Response('Not found', status=404)

    cartogram_entry = CartogramEntry.query.filter_by(string_key=string_key).first_or_404()

    if cartogram_entry is None or cartogram_entry.handler not in cartogram_handlers:
        return Response('Error', status=500)
    
    cartogram_entry.date_accessed = datetime.datetime.utcnow()
    db.session.commit()    
    
    cartogram_handlers_select = {}

    for key, handler in cartogram_handlers.items():
        for selector_name in handler.selector_names():
            cartogram_handlers_select[key] = selector_name

    dict(sorted(cartogram_handlers_select.items()))

    return render_template('cartogram.html', page_active='cartogram', 
                           maps=cartogram_handlers_select,
                           map_name=cartogram_entry.handler, map_data_key=string_key,
                           tracking=tracking.determine_tracking_action(request))


@app.route('/embed/map/<map_name>', methods=['GET'])
def cartogram_embed_by_map(map_name):

    if map_name not in cartogram_handlers:
        return Response('Error', status=500)

    return render_template('embed.html', page_active='cartogram', 
                           map_name=map_name,
                           mode='embed', tracking=tracking.determine_tracking_action(request))

@app.route('/embed/cart/<string_key>', methods=['GET'])
def cartogram_embed_by_key(string_key):
    if not settings.USE_DATABASE:
        return Response('Not found', status=404)

    cartogram_entry = CartogramEntry.query.filter_by(string_key=string_key).first_or_404()

    if cartogram_entry.handler not in cartogram_handlers:
        return Response('Error', status=500)
    
    if cartogram_entry != None:
        cartogram_entry.date_accessed = datetime.datetime.utcnow()
        db.session.commit()

    return render_template('embed.html', page_active='cartogram', 
                        map_name=cartogram_entry.handler, map_data_key=string_key,
                        mode='embed', tracking=tracking.determine_tracking_action(request))


@app.route('/setprogress', methods=['POST'])
def setprogress():
    params = json.loads(request.data)

    if params['secret'] != settings.CARTOGRAM_PROGRESS_SECRET:
        return Response("", status=200)

    current_progress = redis_conn.get("cartprogress-{}".format(params['key']))

    if current_progress is None:

        current_progress = {
            'order': params['order'],
            'stderr': params['stderr'],
            'progress': params['progress']
        }

    else:

        current_progress = json.loads(current_progress.decode())

        if current_progress['order'] < params['order']:
            current_progress = {
                'order': params['order'],
                'stderr': params['stderr'],
                'progress': params['progress']
            }

    redis_conn.set("cartprogress-{}".format(params['key']), json.dumps(current_progress))
    redis_conn.expire("cartprogress-{}".format(params['key']), 300)

    return Response('', status=200)


@app.route('/getprogress', methods=['GET'])
def getprogress():
    current_progress = redis_conn.get("cartprogress-{}".format(request.args["key"]))

    if current_progress == None:
        return Response(json.dumps({'progress': None, 'stderr': ''}), status=200, content_type='application/json')
    else:
        current_progress = json.loads(current_progress.decode())
        return Response(json.dumps({'progress': current_progress['progress'], 'stderr': current_progress['stderr']}),
                        status=200, content_type='application/json')


@app.route('/cartogram', methods=['POST'])
def cartogram():    
    colName = 0
    colColor = 1
    colValue = 2 # Starting column of data

    try:
        data = json.loads(request.form['data'])
        handler = data['handler']
        cartogram_handler = cartogram_handlers[handler]

        if 'handler' not in data or data['handler'] not in cartogram_handlers:
            return Response('{"error":The handler was invaild."}', status=400, content_type="application/json")

        if 'stringKey' not in data:
            return Response('{"error":"Missing sharing key."}', status=404, content_type="application/json")

        string_key = data['stringKey']
        cart_data = cartogram_handler.get_area_string_and_colors(data)
        lambda_result = awslambda.generate_cartogram(cart_data[0],
                            cartogram_handler.get_gen_file(), settings.CARTOGRAM_LAMBDA_URL,
                            settings.CARTOGRAM_LAMDA_API_KEY, string_key)

        cartogram_gen_output = lambda_result['stdout']

        if cartogram_handler.expect_geojson_output():
            # Just confirm that we've been given valid JSON. Calculate the extrema if necessary
            cartogram_json = json.loads(cartogram_gen_output)

            if "bbox" not in cartogram_json:
                cartogram_json["bbox"] = geojson_extrema.get_extrema_from_geojson(cartogram_json)
        else:
            cartogram_json = gen2dict.translate(io.StringIO(cartogram_gen_output), settings.CARTOGRAM_COLOR,
                                                cartogram_handler.remove_holes())
            
        cartogram_json['tooltip'] = cart_data[2]

        with open("static/userdata/" + string_key + ".json", "w") as outfile:
            outfile.write(json.dumps({'{}-custom'.format(colValue): cartogram_json}))

        if settings.USE_DATABASE:
            new_cartogram_entry = CartogramEntry(string_key=string_key, date_created=datetime.datetime.today(),
                                    handler=handler, areas_string='-',
                                    cartogram_data='-', cartogramui_data=json.dumps({"colors": cart_data[1]}))
            db.session.add(new_cartogram_entry)
            db.session.commit()

        return get_mappack_by_key(string_key, False)
    
    except (KeyError, csv.Error, ValueError, UnicodeDecodeError):
        return Response('{"error":"The data was invalid."}', status=400, content_type="application/json")
    except Exception as e:
        return Response('{"error":"{}"}'.format(e), status=400, content_type="application/json")    

@app.route('/mappack/<string_key>', methods=['GET'])
def get_mappack_by_key(string_key, updateaccess = True):
    if not settings.USE_DATABASE:
        return Response('Not found', status=404)

    cartogram_entry = CartogramEntry.query.filter_by(string_key=string_key).first_or_404()

    if cartogram_entry == None or cartogram_entry.handler not in cartogram_handlers:
        return Response('Error', status=500)
    
    if updateaccess:
        cartogram_entry.date_accessed = datetime.datetime.utcnow()
        db.session.commit()

    mappack = json.loads(cartogram_entry.cartogramui_data)
    with open("static/cartdata/{}/mappack.json".format(cartogram_entry.handler), "r") as file:
        original_mappack = json.load(file)
        for item in ["abbreviations", "config", "labels", "original"]:
            mappack[item] = original_mappack[item]

    with open("static/userdata/{}.json".format(cartogram_entry.string_key), "r") as file:
        new_maps = json.load(file)
        mappack.update(new_maps)
        data_names = list(new_maps.keys())
        data_names.insert(0, "original")
        mappack["config"]["data_names"] = data_names

    mappack['stringKey'] = string_key

    return Response(json.dumps(mappack), content_type='application/json', status=200)

@app.route('/cleanup')
def cleanup():
    if settings.USE_DATABASE:
        year_ago = datetime.datetime.utcnow() - datetime.timedelta(days=366)
        CartogramEntry.query.filter(CartogramEntry.date_accessed < year_ago).delete()
        db.session.commit()
        return Response(year_ago, status=200)

if __name__ == '__main__':
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
