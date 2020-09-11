from mongoengine import *
from flask_login import UserMixin
from bson.json_util import dumps
from dotenv import load_dotenv
import os, datetime, calendar

load_dotenv()

if os.getenv("FLASK_ENV") == "development":
    db = connect('djenda-test-database')
else:
    db = connect(host=os.getenv("DB_URI"))

class UserType:
    ENREGISTRER  = "enregistrer"
    ADMIN = "admin"

class CustomDateTimeField(DateTimeField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def to_json(self):
        return str("dyglo")


class PlanType:
    GRATUIT = {"NOM" : "GRATUIT", "NBR_ARTICLES" : 4}
    STANDARD = {"NOM" : "STANDARD", "NBR_ARTICLES" : 30}
    GOLD = {"NOM" : "GOLD", "NBR_ARTICLES" : 100}

class Plan(Document):
    nbr_articles_restant = IntField(required=True, default=PlanType.GRATUIT["NBR_ARTICLES"])
    type = StringField(required=True, default=PlanType.GRATUIT["NOM"])
    timestamp_end = DateTimeField(required=True)
    end_at = StringField(required=True)
    user = ReferenceField('User')

    def set_user(self, user):
        self.user = user
        self.save()

    @staticmethod
    def create(plan_type=PlanType.GRATUIT):
        end_date = Plan.end_date(plan_type)
        plan = Plan(type=plan_type["NOM"],
                    nbr_articles_restant=plan_type["NBR_ARTICLES"],
                    timestamp_end=end_date,
                    end_at=str(end_date))
        plan.save()
        return plan

    def is_ended(self):
        if datetime.datetime.now() > self.timestamp_end:
            return True
        else:
            return False


    @staticmethod
    def end_date(plan_type=PlanType.GRATUIT):
        now = datetime.datetime.now()
        if plan_type["NOM"] == PlanType.GRATUIT["NOM"]:
            month_end_day = calendar.monthrange(now.year, now.month)[1]
            return datetime.datetime(now.year, now.month, month_end_day)
        else:
            return now + datetime.timedelta(days=30)

    def can_post_article(self):
        if self.nbr_articles_restant > 0:
            return True
        return False

    def post_article(self):
        if self.can_post_article():
            self.nbr_articles_restant -= 1
            self.save()
        else:
            raise ValueError("Nombre articles restant 0")


class Produit(Document):
    categorie = StringField(required=True, max_length=50)
    vendeur_id = StringField(required=True)
    prix = IntField(required=True)
    description = StringField(required=True, max_length=200)
    url_photo = StringField(required=True)
    url_thumbnail_photo = StringField(required=True)
    location = GeoPointField(required=True)
    timestamp = DateTimeField(required=True, default=datetime.datetime.utcnow())
    created_at = StringField(required=True, default=str(datetime.datetime.utcnow()))

    @staticmethod
    def product_from_dict(dict):
        data_time = datetime.datetime.utcnow()
        return Produit(prix=dict['prix'],
                       vendeur_id="",
                       categorie=dict['categorie'],
                       description=dict['description'],
                       url_photo=dict['url_photo'],
                       url_thumbnail_photo=dict['url_thumbnail_photo'],
                       timestamp=data_time,
                       created_at=str(data_time),
                       location=[float(dict['longitude']), float(dict['latitude'])])


    @queryset_manager
    def order_by_created_desc(doc_cls, queryset):
        return queryset.order_by('-timestamp')

    @staticmethod
    def near_order_by_created_desc(loc=[0, 0], max_distance=1000):
        return Produit.order_by_created_desc.filter(location__near=loc, location__max_distance=max_distance)

    @staticmethod
    def near_order_by_distance(loc=[0, 0], max_distance=1000):
        return Produit.objects.filter(location__near=loc, location__max_distance=max_distance).order_by('location')

    @staticmethod
    def page(page_nb=1, items_per_page=20):
        offset = (page_nb - 1) * items_per_page
        return Produit.objects.skip( offset ).limit( items_per_page )

    @staticmethod
    def best_match(loc=[0, 0], max_distance=1000, nbr=100):
        return Produit.near_order_by_distance(loc=loc, max_distance=max_distance).limit(nbr).order_by('-timestamp')

class User(Document, UserMixin):
    unique_id = StringField(required=True)
    nom = StringField(required=True, min_length=3, max_length=50)
    phone_number =StringField(min_length=10, max_length=13)
    email = EmailField(required=True, min_length=10)
    url_photo = URLField(required=True, min_length=10)
    localisation = GeoPointField()
    produits = ListField(ReferenceField(Produit))
    plan = ReferenceField(Plan)

    def from_user_info(user_info):
        user =  User(unique_id = str(user_info["sub"]),
                     nom = user_info["given_name"],
                     email = user_info["email"],
                     url_photo = user_info["picture"])
        user.save()
        user.set_plan(Plan.create())
        return user

    def can_post_article(self):
        return self.plan.can_post_article()

    def nbr_articles_restant(self):
        return self.plan.nbr_articles_restant

    def set_plan(self, plan):
        plan.set_user(self)
        self.plan = plan
        self.save()

    def add_article_from_dict(self, dict):
        produit = Produit.product_from_dict(dict)
        self.add_article(produit)
        return produit

    def add_article(self, article):
        self.refresh_plan_if_end()
        self.plan.post_article()
        article.vendeur_id = self.unique_id
        article.save()
        self.produits.append(article)
        self.save()
        return article

    def refresh_plan_if_end(self):
        if self.plan.is_ended():
            self.set_plan(Plan.create())

    def articles_to_json(self):
        return Produit.objects(vendeur_id=self.unique_id).to_json()

    def get_id(self):
        return self.unique_id
