from .model import *
import random

class FakeData:

    @staticmethod
    def email():
         return random.choice(['techalchimiste@gmail.com',
                               'glodymbutwile@gmail.com',
                               'elimulaja@gmail.com'])

    @staticmethod
    def nom_user():
         return random.choice(['glody', 'eli','alchimiste'])

    @staticmethod
    def url_photo():
         return "https://res.cloudinary.com/alchemist118/image/upload/v1594291814/djenda/image-placeholder_sgrgq3.jpg"

    @staticmethod
    def categorie():
         return random.choice(['telephone', 'ordinateur', 'jeux', 'fashion'])

    @staticmethod
    def nom_article():
         return random.choice(['iphone 6', 'samsung','hp', 'dell', 'polo', 'ps4'])

    @staticmethod
    def prix():
         return random.choice([20, 30, 40,50,70,150, 200])

    @staticmethod
    def description():
         return random.choice(['lorem ipsum dolor', 'nike rouge', '500 Gb ram 4 Gb'])

    @staticmethod
    def id():
        return random.randint(1, 10000)

    @staticmethod
    def user(id=None):
        if id == None:
            id = FakeData.id()
        return User(unique_id=str(id),
                    nom = FakeData.nom_user(),
                    email = FakeData.email(),
                    url_photo = FakeData.url_photo())

    @staticmethod
    def article():
        return Produit(nom=FakeData.nom_article(),
                       prix=FakeData.prix(),
                       categorie=FakeData.categorie(),
                       description=FakeData.description(),
                       url_photo=FakeData.url_photo())

    @staticmethod
    def users():
        users = []
        emails = set()
        while len(users) < 2:
            user = FakeData.user()
            if not user.email in emails:
                emails.add(user.email)
                users.append(user)
        return users

    @staticmethod
    def add_user_to_database():
        for user in FakeData.users():
            user.save()

    @staticmethod
    def articles(nbr=1):
        articles = []
        for i in range(nbr):
            articles.append(FakeData.article())
        return articles

    @staticmethod
    def add_article_to_database(nbr=1):
        articles = FakeData.articles(nbr)
        for article in articles:
            article.save()
        return articles

    @staticmethod
    def gerate_and_insert_articles():
        print('Articles ')
        for article in FakeData.articles():
            print('nom: ', article.nom, ' categorie: ', article.categorie)

        FakeData.add_article_to_database(20)

    @staticmethod
    def gerate_and_insert_user_with_articles():
        print('User ')
        user = FakeData.user(id=1)
        print('nom: ', user.nom, ' id: ', user.unique_id)
        for article in FakeData.add_article_to_database(10):
            user.produits.append(article)
            print('nom: ', article.nom, ' categorie: ', article.categorie)
        user.save()


if __name__ == '__main__':
    print(FakeData.gerate_and_insert_user_with_articles())
