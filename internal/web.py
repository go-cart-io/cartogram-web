#!/usr/bin/env python
import json
import datetime
import os
import shutil
from flask import Flask, request, Response, render_template
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

import cartogram
import settings
import util
from database import db
from handler import CartogramHandler
from asset import Asset
from views import contact, tracking, custom_captcha

def create_app():
    app = Flask(__name__)
    Asset(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    limiter = Limiter(get_remote_address, app=app, default_limits=["50 per hour"], 
                    storage_uri='redis://{}:{}'.format(settings.CARTOGRAM_REDIS_HOST, settings.CARTOGRAM_REDIS_PORT))

    app.app_context().push()
    app.secret_key = settings.SECRET_KEY
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
    # This gets rid of an annoying Flask error message. We don't need this feature anyway.
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['ENV'] = 'development' if settings.DEBUG else 'production'
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB
    app.config['MAX_FORM_MEMORY_SIZE'] = 10 * 1024 * 1024

    if settings.USE_DATABASE:
        from database import db
        from models import CartogramEntry
        db.init_app(app)
        migrate = Migrate(app, db)
        
        try:
            db.create_all()
        except Exception as err:
            print(err)

    default_cartogram_handler = 'usa'
    cartogram_handler = CartogramHandler()

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


    app.add_url_rule('/contact', methods=['GET', 'POST'], view_func=contact.contact)
    app.add_url_rule('/api/v1/consent', methods=['POST'], view_func=tracking.consent)
    app.add_url_rule('/api/v1/gencaptcha', methods=['GET'], view_func=custom_captcha.gencaptcha)


    @app.route('/cartogram', methods=['GET'])
    def get_cartogram():
        return get_cartogram_by_name(default_cartogram_handler, None)


    @app.route('/cartogram/map/<map_name>', methods=['GET'], defaults={'mode': None})
    @app.route('/cartogram/map/<map_name>/<mode>', methods=['GET'])
    def get_cartogram_by_name(map_name, mode):
        if mode == 'embed':
            template = 'embed.html'
        else:
            template = 'cartogram.html'

        if not cartogram_handler.has_handler(map_name):
            return Response('Cannot find the map {}'.format(map_name), status=500)

        return render_template(template, page_active='cartogram', 
                            maps=cartogram_handler.get_sorted_handler_names(),
                            map_name=map_name,
                            mode=mode, tracking=tracking.determine_tracking_action(request))

    @app.route('/cartogram/key/<string_key>', methods=['GET'], defaults={'mode': None})
    @app.route('/cartogram/key/<string_key>/<mode>', methods=['GET'])
    def cartogram_by_key(string_key, mode):
        if mode == 'embed':
            template = 'embed.html'
        else:
            template = 'cartogram.html'

        if not settings.USE_DATABASE:
            return Response('Not found', status=404)

        cartogram_entry = CartogramEntry.query.filter_by(string_key=string_key).first_or_404()

        if cartogram_entry is None or (not cartogram_handler.has_handler(cartogram_entry.handler) and cartogram_entry.handler != 'custom'):
            return Response('Error', status=500)
        
        if mode != 'preview':
            cartogram_entry.date_accessed = datetime.datetime.now(datetime.UTC)
            db.session.commit()    

        return render_template(template, page_active='cartogram', 
                            maps=cartogram_handler.get_sorted_handler_names(),
                            map_name=cartogram_entry.handler, map_data_key=string_key,
                            map_title=cartogram_entry.title, map_color_scheme=cartogram_entry.scheme,
                            mode=mode, tracking=tracking.determine_tracking_action(request))

    @app.route('/api/v1/getprogress', methods=['GET'])
    @limiter.exempt
    def getprogress():
        current_progress_output = cartogram.getprogress(request.args['key'])
        return Response(json.dumps(current_progress_output), status=200, content_type='application/json')

    def cartogram_rate_limit():
        return settings.CARTOGRAM_RATE_LIMIT
    
    @app.route('/cartogram/create', methods=['GET'])
    def create_cartogram():
        return render_template('maker.html', page_active='maker', 
                            maps=cartogram_handler.get_sorted_handler_names(),
                            tracking=tracking.determine_tracking_action(request))
    
    @app.route('/cartogram/edit/<type>/<name_or_key>', methods=['GET'])
    def edit_cartogram(type, name_or_key):
        if type == 'map':
            handler = name_or_key
            csv_url = f'/static/cartdata/{handler}/data.csv'
            title = name_or_key
            scheme = 'pastel1'

        elif type == 'key':
            if not settings.USE_DATABASE:
                return Response('Not found', status=404)

            cartogram_entry = CartogramEntry.query.filter_by(string_key=name_or_key).first_or_404()
            if cartogram_entry is None or (not cartogram_handler.has_handler(cartogram_entry.handler) and cartogram_entry.handler != 'custom'):
                return Response('Error', status=500)

            handler = cartogram_entry.handler
            csv_url = f'/static/userdata/{name_or_key}/data.csv'
            title = cartogram_entry.title
            scheme = cartogram_entry.scheme if cartogram_entry.scheme else 'pastel1'

        else:
            return Response('Not found', status=404)
        
        geo_url = cartogram_handler.get_gen_file(handler, name_or_key)[1:]
        
        return render_template('maker.html', page_active='maker',
                maps=cartogram_handler.get_sorted_handler_names(),
                map_name=handler, geo_url=geo_url, csv_url=csv_url,
                map_title=title, map_color_scheme=scheme,
                tracking=tracking.determine_tracking_action(request))
    
    @app.route('/api/v1/cartogram/preprocess/<mapDBKey>', methods=['POST'])
    def cartogram_preprocess(mapDBKey):
        if mapDBKey is None or mapDBKey == '':
            return Response('{"error":"Missing sharing key."}', status=404, content_type='application/json')
   
        if 'file' not in request.files or request.files['file'].filename == '':
            return Response('{"error": "No selected file"}', status=400, content_type='application/json')
    
        try:
            processed_geojson = cartogram.preprocess(request.files['file'], mapDBKey)
            return Response(json.dumps(processed_geojson), status=200, content_type='application/json')
        except Exception as e:
            return Response(json.dumps({"error": str(e)}), status=400, content_type='application/json')

    @app.route('/api/v1/cartogram', methods=['POST'])
    @limiter.limit(cartogram_rate_limit)
    def cartogram_gen():
        data = json.loads(request.form['data'])
        handler = data['handler']

        if 'handler' not in data or (not cartogram_handler.has_handler(handler) and handler != 'custom'):
            return Response('{"error":"Invalid map."}', status=400, content_type='application/json')

        if 'mapDBKey' not in data:
            return Response('{"error":"Missing sharing key."}', status=404, content_type='application/json')
        
        datacsv = data['csv'] if 'csv' in data else util.get_csv(data)
        string_key = data['mapDBKey']
        userdata_path = None
        clean_by = None

        # Prepare data.csv and Input.json in userdata
        # TODO check whether the code works properly if persist is false
        if 'persist' in data:
            userdata_path = f"static/userdata/{string_key}"
            os.mkdir(userdata_path)
        else:
            userdata_path = f"/tmp/{string_key}"

        with open(f'{userdata_path}/data.csv', 'w') as outfile:
            outfile.write(datacsv)

        gen_file = cartogram_handler.get_gen_file(handler, string_key)

        if handler == 'custom':
            input_path = f"{userdata_path}/Input.json"
            if ('editedFrom' in data and data['editedFrom'] != '' and 
                data['editedFrom'] != input_path and os.path.exists(data['editedFrom'])):
                    shutil.copyfile(data['editedFrom'], input_path)

            else:
                if os.path.exists(f"/tmp/{string_key}.json"):
                    shutil.move(f"/tmp/{string_key}.json", input_path)
                clean_by = data.get('geojsonRegionCol', 'Region')

        try:
            cartogram.generate_cartogram(datacsv, gen_file, data['mapDBKey'], userdata_path, clean_by=clean_by)
                        
            if 'persist' in data and settings.USE_DATABASE:
                new_cartogram_entry = CartogramEntry(string_key=string_key, date_created=datetime.datetime.today(),
                                        date_accessed=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=365),
                                        title=data['title'],scheme=data['scheme'],handler=handler)
                db.session.add(new_cartogram_entry)
                db.session.commit()
            else:
                string_key = None

            return Response(json.dumps({"mapDBKey": string_key}), status=200, content_type='application/json')
        
        # except (KeyError, csv.Error, ValueError, UnicodeDecodeError):
        #     return Response('{"error":"The data was invalid."}', status=400, content_type='application/json')
        except Exception as e:
            if os.path.exists(userdata_path):
                shutil.rmtree(userdata_path)

            return Response(json.dumps({"error": str(e)}), status=400, content_type='application/json')

    @app.route('/cleanup', methods=['GET'])
    def cleanup():
        # Delete records in the database and files that the accessed date is older than 1 year
        num_records = 0
        year_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=366)
        if settings.USE_DATABASE:
            records = CartogramEntry.query.filter(CartogramEntry.date_accessed < year_ago).all()
            num_records = len(records)
            for record in records:
                folder_path = f'static/userdata/{record.string_key}'
                if os.path.exists(folder_path):
                    shutil.rmtree(folder_path)
                db.session.delete(record)

            db.session.commit()

        # Delete files in folder /tmp that the created date is older than 1 days
        for file in os.listdir('/tmp'):
            file_path = os.path.join('/tmp', file)
            days_ago = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=1)
            try:
                if os.path.isfile(file_path) and os.stat(file_path).st_mtime < days_ago.timestamp():
                    os.unlink(file_path)
            except Exception as e:
                print(e)
            
        return "{} ({} records)".format(year_ago.strftime('%d %B %Y - %H:%M:%S'), num_records)
                    
    @app.route('/cart/<key>', methods=['GET'])
    @app.route('/embed/map/<key>', methods=['GET'])
    @app.route('/embed/cart/<key>', methods=['GET'])
    def cartogram_old(key):
        return render_template('404_code_expired.html', title = 'Outdated share/embed code'), 404


    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=settings.DEBUG, host=settings.HOST, port=settings.PORT)
