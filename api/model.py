from mongoengine import *
from flask_login import UserMixin
from bson.json_util import dumps

#connect('djenda-database')
DB_URI = "mongodb+srv://djendambutwile:vNlxq847WPGS8hJI@cluster0.63vlj.mongodb.net/test?retryWrites=true&w=majority"

db = connect(host=DB_URI)
#db = connect('djenda-test-database')
#connect('project1', host='mongodb://heroku_dmv1wxhc:pgung11fd5un3qunjfj8jmfuo2@ds139614.mlab.com:39614/heroku_dmv1wxhc')

class UserType:
    ENREGISTRER  = "enregistrer"
    ADMIN = "admin"


class Produit(Document):
    nom = StringField(required=True, max_length=50)
    categorie = StringField(required=True, max_length=50)
    prix = IntField(required=True)
    description = StringField(required=True, max_length=200)
    url_photo = StringField(required=True)
    url_thumbnail_photo = StringField(required=True)
    location = GeoPointField(required=True)

    @staticmethod
    def product_from_dict(dict):
        return Produit(nom=dict.json['nom'],
                       prix=dict.json['prix'],
                       categorie=dict.json['categorie'],
                       description=dict.json['description'],
                       url_photo=dict.json['url_photo'],
                       url_thumbnail_photo=dict.json['url_thumbnail_photo'],
                       location=[float(dict.json['longitude']), float(dict.json['latitude'])])



class User(Document, UserMixin):
    unique_id = StringField(required=True)
    nom = StringField(required=True, min_length=3, max_length=50)
    email = EmailField(required=True, min_length=10)
    url_photo = URLField(required=True, min_length=10)
    localisation = GeoPointField()
    produits = ListField(ReferenceField(Produit))

    def articles_to_json(self):
        articles_datas = []
        for article in self.produits:
            articles_datas.append(article._data)
        return dumps(articles_datas)

    def get_id(self):
        return self.unique_id
