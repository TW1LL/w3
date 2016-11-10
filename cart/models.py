from django.db import models


class Product(models.Model):

    name = models.CharField(max_length=255)
    image = models.CharField(max_length=255, default="cart/images/cross-sect.jpg")
    description = models.TextField(default="This is a cool looking watch")
    on_hand = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    class Meta:
        abstract = True

    def update_on_hand(self, amount):
        self.on_hand = self.on_hand + amount

    def __str__(self):
        return self.name

    @staticmethod
    def subcategories():
        categories = []
        for cls in Product.__subclasses__():
            categories.append({"name": cls.__name__, "image": cls.cat_img, "description": cls.cat_description})
        return categories


class Part(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True)
    on_hand = models.IntegerField()
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def update_on_hand(self, amount):
        self.on_hand = self.on_hand + amount

    def __str__(self):
        return self.name


class Watch(Product):

    cat_img = "watches/img.jpg"
    cat_description = "Sweet wristpieces that hold time."
    parts = models.ManyToManyField(Part, null=True)


class PaintBall(Product):

    cat_img = "paintball/img.jpg"
    cat_description = "Sweet gats yo."


class ShoppingCart(models.Model):
    owner = models.ForeignKey('auth.user')
    item = models.ForeignKey(Watch, null=True)
    quantity = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.owner.username + "'s item - " + str(self.quantity)