from mongoengine import *
from flask_login import UserMixin


connect('djenda-database')

class UserType:
    ENREGISTRER  = "enregistrer"
    ADMIN = "admin"


class Produit(Document):
    nom = StringField(required=True, max_length=50)
    categorie = StringField(required=True, max_length=50)
    prix = IntField(required=True)
    description = StringField(required=True, max_length=200)
    url_photo = StringField(required=True)

class User(Document, UserMixin):
    unique_id = StringField(required=True,min_length=10)
    nom = StringField(required=True, min_length=3, max_length=50)
    email = EmailField(required=True, min_length=10)
    url_photo = URLField(required=True, min_length=10)
    localisation = GeoPointField()
    produits = ListField(ReferenceField(Produit))

    def get_id(self):
        return self.unique_id
