from django.db import models

# Create your models here.

class SiteConfig(models.Model):
    title = models.CharField(max_length=255)
    slogan = models.CharField(max_length=255)


class Part(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True)
    on_hand = models.IntegerField()
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def update_on_hand(self, amount):
        self.on_hand = self.on_hand + amount

    def __str__(self):
        return self.name


class Watch(models.Model):
    name = models.CharField(max_length=255)
    image = models.CharField(max_length=255, default="cart/images/cross-sect.jpg")
    parts = models.ManyToManyField(Part, null=True)
    description = models.TextField(default="This is a cool looking watch")
    on_hand = models.IntegerField()
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def update_on_hand(self, amount):
        self.on_hand = self.on_hand + amount

    def __str__(self):
        return self.name


class ShoppingCart(models.Model):
    owner = models.ForeignKey('auth.user')
    item = models.ForeignKey(Watch, null=True)
    quantity = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.owner.username + "'s item - " + str(self.quantity)

