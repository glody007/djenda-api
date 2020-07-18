from flask import (
    Flask,
    jsonify,
    abort,
    make_response,
    request,
    redirect,
    render_template,
    url_for
)

from flask_cors import CORS
# Python standard libraries
import json
import os


from flask_login import (
    LoginManager,
    current_user,
    login_required,
    login_user,
    logout_user,
)
from oauthlib.oauth2 import WebApplicationClient
import requests

from .model import User, Produit, UserType

# configuration
DEBUG = True

# Configuration
#GOOGLE_CLIENT_ID = os.environ.get("1046255643666-j2lnved5a6slg15ibac6srr4um3k85vp.apps.googleusercontent.com", None)
#GOOGLE_CLIENT_SECRET = os.environ.get("vvzB8F3CG199NKZIWHZfSwmg", None)
GOOGLE_CLIENT_ID = "1046255643666-j2lnved5a6slg15ibac6srr4um3k85vp.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "vvzB8F3CG199NKZIWHZfSwmg"
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

# instantiate the app
app = Flask(__name__)
app.config.from_object(__name__)

app.secret_key = os.environ.get("SECRET_KEY") or os.urandom(24)

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)

# OAuth 2 client setup
client = WebApplicationClient(GOOGLE_CLIENT_ID)

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

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
    if current_user.is_authenticated:
        return (
            "<p>Hello, {}! You're logged in! Email: {}</p>"
            "<div><p>Google Profile Picture:</p>"
            '<img src="{}" alt="Google profile pic"></img></div>'
            '<a class="button" href="/logout">Logout</a>'.format(
                current_user.nom, current_user.email, current_user.photo
            )
        )
    else:
        reponse = '<a class="button" href="/login">Google Login</a>'
        return jsonify({'nom' : 'alchimiste'})

@app.route("/user")
def user():
    return jsonify({'nom' : 'alchimiste'})


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()

# Flask-Login helper to retrieve a user from our db
@login_manager.user_loader
def load_user(user_id):
    return User.objects(unique_id=user_id).first()

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
        auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
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
                    photo = userinfo_response.json()["picture"])
    else:
        return "User email not available or not verified by Google.", 400

    # Doesn't exist? Add it to the database.
    if not User.objects(unique_id=unique_id).first():
        user.save()

    login_user(user)

    return redirect(url_for("index"))

@app.route('/users', methods=['GET'])
def all_users():
    return User.objects().to_json()

@app.route('/users/<id>', methods=['GET'])
def get_user(numero):
    user = User.objects(unique_id=id).first()
    if user == None:
        abort(404)
    return user.to_json()

@app.route('/users/<id>/produits', methods=['GET'])
def get_user_produits(id):
    user = User.objects(unique_id=id).first()
    if user == None:
        abort(404)
    return user.articles_to_json()

@app.route('/users/<id>/produits', methods=['POST'])
def add_produit(id):
    if (not request.json or
        not request.json['prix'] or
        not request.json['nom'] or
        not request.json['categorie'] or
        not request.json['description']):
        abort(400)
    user = User.objects(unique_id=id).first()
    if user == None:
        abort(404)
    produit = Produit(nom=request.json['nom'],
                      prix=request.json['prix'],
                      categorie=request.json['categorie'],
                      description=request.json['description'],
                      url_photo=request.json['url_photo']).save()
    user.produits.append(produit)
    user.save()
    return user.articles_to_json()

@app.route('/produits', methods=['POST'])
def add_produit_only():
    if (not request.json or
        not request.json['prix'] or
        not request.json['nom'] or
        not request.json['categorie'] or
        not request.json['description']):
        abort(400)
    user = None
    if not User.objects(unique_id=1).first():
        user = User(unique_id = 1,
                    nom ="alchimiste",
                    email = "djendambutwile@gmail.com",
                    url_photo = "https://res.cloudinary.com/alchemist118/image/upload/w_100,h_100/v1595080373/mario.jpg")
    produit = Produit(nom=request.json['nom'],
                      prix=request.json['prix'],
                      categorie=request.json['categorie'],
                      description=request.json['description'],
                      url_photo="https://res.cloudinary.com/alchemist118/image/upload/w_100,h_100/v1595080373/mario.jpg"]).save()
    user.produits.append(produit)
    user.save()
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

    if (not request.json or
        not request.json['prix'] or
        not request.json['nom'] or
        not request.json['categorie'] or
        not request.json['description']):
        abort(400)

    produit = Produit.objects(id=id).first()
    if produit == None:
        abort(404)

    produit.nom = request.json['nom']
    produit.prix = request.json['prix'],
    produit.categorie = request.json['categorie'],
    produit.description = request.json['description']
    produit.save()

    return jsonify({'produit': produit.to_json()}), 201

if __name__ == '__main__':
    app.run()
