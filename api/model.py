from mongoengine import *
from flask_login import UserMixin
from bson.json_util import dumps
from dotenv import load_dotenv
import os

load_dotenv()

if os.getenv("FLASK_ENV") == "development":
    db = db = connect('djenda-test-database')
else:
    db = connect(host=os.getenv("DB_URI"))

class UserType:
    ENREGISTRER  = "enregistrer"
    ADMIN = "admin"


class Produit(Document):
    nom = StringField(required=True, max_length=50)
    categorie = StringField(required=True, max_length=50)
    vendeur_id = StringField(required=True)
    prix = IntField(required=True)
    description = StringField(required=True, max_length=200)
    url_photo = StringField(required=True)
    url_thumbnail_photo = StringField(required=True)
    location = GeoPointField(required=True)

    @staticmethod
    def product_from_dict(dict):
        return Produit(nom=dict['nom'],
                       prix=dict['prix'],
                       vendeur_id="",
                       categorie=dict['categorie'],
                       description=dict['description'],
                       url_photo=dict['url_photo'],
                       url_thumbnail_photo=dict['url_thumbnail_photo'],
                       location=[float(dict['longitude']), float(dict['latitude'])])



class User(Document, UserMixin):
    unique_id = StringField(required=True)
    nom = StringField(required=True, min_length=3, max_length=50)
    phone_number =StringField(min_length=10, max_length=13)
    email = EmailField(required=True, min_length=10)
    url_photo = URLField(required=True, min_length=10)
    localisation = GeoPointField()
    produits = ListField(ReferenceField(Produit))

    def add_article_from_dict(self, dict):
        produit = Produit.product_from_dict(dict)
        self.add_article(produit)
        return produit

    def add_article(self, article):
        article.vendeur_id = self.unique_id
        article.save()
        self.produits.append(article)
        self.save()
        return article

    def articles_to_json(self):
        return Produit.objects(vendeur_id=self.unique_id).to_json()

    def get_id(self):
        return self.unique_id
