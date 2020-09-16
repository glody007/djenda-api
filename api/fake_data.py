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
         return "https://ik.imagekit.io/djenda/Djenda_M8A0w1OWcA"

    @staticmethod
    def url_thumbnail_photo():
         return "https://ik.imagekit.io/djenda/tr:n-media_library_thumbnail/Djenda_M8A0w1OWcA"

    @staticmethod
    def categorie():
         return random.choice(['telephone', 'ordinateur', 'jeux', 'fashion'])

    @staticmethod
    def nom_article():
         return random.choice(['iphone 6', 'samsung','hp', 'dell', 'polo', 'ps4'])

    @staticmethod
    def phone_number():
         return random.choice(['+243997028901'])

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
        return User.insert(User(unique_id=str(id),
                            nom = FakeData.nom_user(),
                            email = FakeData.email(),
                            phone_number = FakeData.phone_number(),
                            url_photo = FakeData.url_photo()), PlanType.GOLD)

    @staticmethod
    def location():
        return random.choice([[10.5, -10.4], [2.4, 5], [4, 20], [20, 30]])


    @staticmethod
    def article():
        data_time = datetime.datetime.utcnow()
        return Produit(prix=FakeData.prix(),
                       vendeur_id="",
                       categorie=FakeData.categorie(),
                       description=FakeData.description(),
                       url_photo=FakeData.url_photo(),
                       timestamp=data_time,
                       created_at=str(data_time),
                       url_thumbnail_photo=FakeData.url_thumbnail_photo(),
                       location=FakeData.location())

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
            print(article.to_json())
            article.save()
        return articles

    @staticmethod
    def gerate_and_insert_articles():
        print('Articles ')
        for article in FakeData.articles():
            print(' created_at: ', article.created_at)

        FakeData.add_article_to_database(20)

    @staticmethod
    def gerate_and_insert_user_with_articles():
        print('User ')
        user = FakeData.user(id=1)
        print('nom: ', user.nom, ' number: ', user.phone_number)
        for article in FakeData.add_article_to_database(20):
            user.add_article(article)
            print('created_at: ', article.created_at)
        print(User.objects(unique_id=str(1)))


if __name__ == '__main__':
    db.drop_database('djenda-test-database')
    print(FakeData.gerate_and_insert_user_with_articles())
    print(Produit.best_match(nbr=5).only("location", "created_at").to_json())
