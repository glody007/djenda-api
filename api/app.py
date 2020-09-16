from flask import (
    Flask,
    jsonify,
    abort,
    make_response,
    session,
    request,
    redirect,
    render_template,
    url_for
)

from flask_cors import CORS
# Python standard libraries
import json
import os
import base64
import sys
import datetime

from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from google.oauth2 import id_token
from google.auth.transport import requests

from .model import User, Produit, UserType

# settings.py
from dotenv import load_dotenv
load_dotenv()

# OR, the same with increased verbosity
load_dotenv(verbose=True)

# OR, explicitly providing path to '.env'
from pathlib import Path  # Python 3.6+ only
env_path = Path('..') / '.env'
load_dotenv(dotenv_path=env_path)

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(
    DEBUG = True,
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24),
    # conigure login_user(remember=True) valid for 7days, default=1year
    REMEMBER_COOKIE_DURATION = datetime.timedelta(days=365),
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID"),
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET"),
    GOOGLE_DISCOVERY_URL = os.getenv("GOOGLE_DISCOVERY_URL"),
    IMAGEKIT_PRIVATE_KEY = os.getenv("IMAGEKIT_PRIVATE_KEY"),
    IMAGEKIT_PUBLIC_KEY = os.getenv("IMAGEKIT_PUBLIC_KEY"),
    IMAGEKIT_URL_ENDPOINT = os.getenv("IMAGEKIT_URL_ENDPOINT")
)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

# enable CORS
CORS(app, resources={r'/*': {'origins': '*'}})

@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

@app.errorhandler(400)
def bad_request(error):
    return make_response(jsonify({'error': 'Bad request'}), 400)


@app.route("/")
def index():
    return ("<p>Welcome to Jjenda</p>")

@app.route("/user")
def user():
    return jsonify({'nom' : 'alchimiste'})


def get_google_provider_cfg():
    return requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.objects(unique_id=str(user_id)).first()

@app.before_request
def before_request():
    session.permanent = True
    app.permanent_session_lifetime = app.config['REMEMBER_COOKIE_DURATION']

@app.route("/login")
def login():
    # Find out what URL to hit for Google login
    google_provider_cfg = get_google_provider_cfg()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Use library to construct the request for Google login and provide
    # scopes that let you retrieve user's profile from Google
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/login/callback")
def callback():
    # Get authorization code Google sent back to you
    code = request.args.get("code")

    # Find out what URL to hit to get tokens that allow you to ask for
    # things on behalf of a user
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare and send a request to get tokens! Yay tokens!
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )

    # Parse the tokens!
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Now that you have tokens (yay) let's find and hit the URL
    # from Google that gives you the user's profile information,
    # including their Google profile image and email
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    # You want to make sure their email is verified.
    # The user authenticated with Google, authorized your
    # app, and now you've verified their email through Google!
    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        user = User(unique_id = userinfo_response.json()["sub"],
                    nom = userinfo_response.json()["given_name"],
                    email = userinfo_response.json()["email"],
                    url_photo = userinfo_response.json()["picture"])
    else:
        return "User email not available or not verified by Google.", 400

    # Doesn't exist? Add it to the database.
    if not User.objects(unique_id=unique_id).first():
        user.save()

    return redirect(url_for("index"))


from twilio.rest import Client

#Initialize Twilio client
client = Client()

def start_verification(to, channel='sms'):
    if channel not in ('sms', 'call'):
        channel = 'sms'

    service = app.config['VERIFICATION_SID']

    verification = client.verify \
        .services(service) \
        .verifications \
        .create(to=to, channel=channel, app_hash=app.config['APP_HASH'])

    return verification.sid

def check_verification(phone, code):
    service = app.config['VERIFICATION_SID']

    try:
        verification_check = client.verify \
            .services(service) \
            .verification_checks \
            .create(to=phone, code=code)

        if verification_check.status == "approved":
            return True

        else:
            return False

    except Exception as e:
        return False

@app.route('/register_number', methods=['POST'])
def register_number():
    current_user.phone_number = request.json['number']
    current_user.save()
    return jsonify({'success': True})

@app.route('/send_verification_code', methods=['POST'])
def send_verifacation_code():
    if start_verification(request.json['number']) is None:
        return jsonify({'success' : False})
    current_user.phone_number = request.json['number']
    return jsonify({'success': True})

@app.route('/check_verification_code', methods=['POST'])
def check_verifacation_code():
    if check_verification(current_user.phone_number, request.json['code']):
        current_user.save()
        return jsonify({'verify' : True})
    else:
        return jsonify({'verify' : False})

@app.route('/has_phone_number', methods=['GET'])
def has_phone_number():
    if not current_user.is_authenticated:
        return jsonify({'has_phone_number' : False})
    if current_user.phone_number is None:
        return jsonify({'has_phone_number' : False})
    else:
        return jsonify({'has_phone_number' : True})


from imagekitio import ImageKit

imagekit = ImageKit(
    private_key=app.config['IMAGEKIT_PRIVATE_KEY'],
    public_key=app.config['IMAGEKIT_PUBLIC_KEY'],
    url_endpoint =app.config['IMAGEKIT_URL_ENDPOINT']
)

@app.route('/auth_endpoint', methods=['GET'])
def auth_endpoint():
    auth_params = imagekit.get_authentication_parameters()

    return jsonify(auth_params)


@app.route('/verify_oauth2_token/<token>', methods=['GET'])
def verify_oauth2_token(token):
    try:
        userinfo_response = id_token.verify_oauth2_token(token, requests.Request(),app.config['GOOGLE_CLIENT_ID'])
        unique_id = userinfo_response["sub"]
        user = User.objects(unique_id=str(unique_id)).first()
        # Doesn't exist? Add it to the database.
        if not user:
            user = User.from_user_info(userinfo_response)

        login_user(user)
        return jsonify({"verify":True})
    except ValueError:
        return jsonify({"verify":False})


@app.route('/users', methods=['GET'])
def all_users():
    return User.objects().to_json()

@app.route('/users/posts_restants', methods=['GET'])
def posts_restants():
    return jsonify({'posts_restants' : current_user.nbr_articles_restant()})

@app.route('/users/<id>', methods=['GET'])
def get_user(id):
    user = User.objects(unique_id=str(id)).first()
    if user == None:
        abort(404)
    return user.to_json()

@app.route('/users/<id>/produits', methods=['GET'])
def get_user_produits(id):
    user = User.objects(unique_id=id).first()
    if user == None:
        abort(404)
    return user.articles_to_json()

def is_product_or_404(request):
    if (not request.json or
        not request.json['prix'] or
        not request.json['categorie'] or
        not request.json['description'] or
        not request.json['url_photo'] or
        not request.json['url_thumbnail_photo'] or
        not request.json['latitude'] or
        not request.json['longitude']):
        abort(400)

@app.route('/users/<id>/produits', methods=['POST'])
def add_produit(id):
    is_product_or_404(request)
    user = User.objects(unique_id=id).first()
    if user == None:
        abort(404)
    user.add_article_from_dict(request.json)
    return user.articles_to_json()

@app.route('/users/produits', methods=['GET'])
def user_produit():
    user = User.objects(unique_id=current_user.unique_id).first()
    if not user:
        abort(404)
    return user.articles_to_json()

@app.route('/produits', methods=['POST'])
def add_user_produit():
    is_product_or_404(request)
    user = User.objects(unique_id=current_user.unique_id).first()
    if not user:
        abort(404)
    user.add_article_from_dict(request.json)
    return user.articles_to_json()

@app.route('/produits', methods=['GET'])
def all_produits():
    return Produit.objects().to_json()

@app.route('/produits/<id>', methods=['DELETE'])
def delete_produit(id):
    produit = Produit.objects(id=id).first()
    if user == None:
        abort(404)
    produit.delete()
    return jsonify({'resultat' : True})

@app.route('/produits/<id>', methods=['PUT'])
def update_produit(id):
    is_product_or_404()

    produit = Produit.objects(id=id).first()
    if produit == None:
        abort(404)

    produit.prix = request.json['prix'],
    produit.categorie = request.json['categorie'],
    produit.description = request.json['description']
    produit.save()

    return jsonify({'produit': produit.to_json()}), 201

if __name__ == '__main__':
    app.run()
