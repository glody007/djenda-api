import unittest, datetime, calendar
from .model import *

info = {"sub": 1,
        "given_name": "alchimiste",
        "email":"jjenda@gmail.com",
        "picture":"https://jjenda.com"}

class TestUser(unittest.TestCase):

    def test_from_user_info(self):
        user = User.from_user_info(info)
        self.assertNotEqual(user.plan, None)

    def test_add_article(self):
        produit_info = {"prix":10, "categorie":"pc",
                        "description":"500gb", "url_photo":"jjenda.com",
                        "url_thumbnail_photo":"jjenda.com",
                        "longitude":10.7, "latitude":1.344}

        user = User.from_user_info(info)
        self.assertEqual(len(user.produits), 0)

        nbr_articles_restant = user.nbr_articles_restant()
        article = Produit.product_from_dict(produit_info)
        article = user.add_article(article)
        self.assertEqual(article.vendeur_id, user.unique_id)
        self.assertEqual(len(user.produits), 1)
        self.assertEqual(user.nbr_articles_restant(), nbr_articles_restant - 1)

        now = datetime.datetime.now()
        user.plan.timestamp_end = now - datetime.timedelta(days=1)
        plan_id_before_adding = user.plan.id
        user.add_article(article)
        plan_id_after_adding = user.plan.id
        self.assertNotEqual(plan_id_before_adding, plan_id_after_adding)

        user.plan.nbr_articles_restant = 0
        self.assertFalse(user.can_post_article())
        with self.assertRaises(ValueError):
            user.add_article(article)

        user = User(unique_id = str(info["sub"]),
                    email=info["email"],
                    nom=info["given_name"],
                    url_photo=info["picture"])
        user.save()
        self.assertEqual(user.plan, None)

        user.add_article(article)
        self.assertNotEqual(user.plan, None)


class TestPlan(unittest.TestCase):

    def test_create(self):
        plan = Plan.create()
        self.assertEqual(plan.type, PlanType.GRATUIT["NOM"])
        self.assertEqual(plan.nbr_articles_restant, PlanType.GRATUIT["NBR_ARTICLES"])
        self.assertNotEqual(plan.id, None)

    def test_end_date(self):
        end_date_plan_gratuit = Plan.end_date()
        self.assertTrue(end_date_plan_gratuit.day in [28, 29, 30, 31])

        end_date = datetime.datetime.now() + datetime.timedelta(days=30)
        end_date_other_plan = Plan.end_date(PlanType.STANDARD)
        self.assertEqual(end_date_other_plan.day, end_date.day)

    def test_can_post_article(self):
        plan = Plan.create()
        self.assertTrue(plan.can_post_article())

        plan.nbr_articles_restant = 0
        self.assertFalse(plan.can_post_article())

    def test_post_article(self):
        plan = Plan.create()
        plan.post_article()
        self.assertEqual(plan.nbr_articles_restant, 3)

        plan.nbr_articles_restant = 1
        plan.post_article()
        self.assertEqual(plan.nbr_articles_restant, 0)

        with self.assertRaises(ValueError):
            plan.post_article()

    def test_is_ended(self):
        plan = Plan.create()
        self.assertFalse(plan.is_ended())

        now = datetime.datetime.now()
        plan.timestamp_end = now - datetime.timedelta(days=1)
        self.assertTrue(plan.is_ended())
