from decimal import Decimal
import json
from datetime import datetime

from django.db import models
from django.utils import timezone

from cart.models import Category, ShoppingCart, CartItem


class Order(models.Model):
    """
    Represents the order from the moment a user checks out, including historically

    To create, you must initialize it with the following args:
    customer= auth.user object
    cart = cart.ShoppingCart object
    date_created = datetime.now()
    date_modified = datetime.now()

    to finalize:
    call .finalize()
    """
    STATUS_CHOICES = {
        "Created": 'Order created',
        "Addressed": 'Order created, Ship Address completed',
        "Shipping Chosen": 'Order created, Ship method chosen',
        "Ready to Ship": 'Payed, addressed, and finalized.',
        "Shipped": 'Order Shipping',
        "Complete": 'Order Complete', # this isn't used because we currently don't confirm delivery
    }

    customer = models.ForeignKey('auth.User')
    cart = models.OneToOneField(ShoppingCart, null=True)
    address = models.ForeignKey('checkout.Address', null=True)
    shipping_object = models.TextField(default=None, null=True)
    payment = models.CharField(null=True, max_length=255, default="None")

    date_created = models.DateTimeField(editable=False)
    date_modified = models.DateTimeField()

    finalized = models.BooleanField(default=False)
    date_finalized = models.DateTimeField(null=True)

    items = models.ManyToManyField(CartItem)
    desc = models.CharField(max_length=255, default="1 Watch")
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    shipping_label = models.TextField(default="None")
    shipping_tracking = models.TextField(default="None")

    def info(self):
        """
        Create purchase object
        :return:
        """
        cart = ShoppingCart.objects.get(id=self.cart_id)
        items = cart.get_cart_items()

        total = {
            'sub': cart.total_price(),
            'shipping': 0,
            'total': 0}

        purchase = {
            'total_qty': 0,
            'qty': cart.count_items(),
            'address': ""
        }

        # Add shipping cost
        if self.shipping_object is not None:
            shipping = json.loads(self.shipping_object)
            total['shipping'] = Decimal(shipping['rate'])

        # grand total
        total['total'] = total['sub'] + total['shipping']
        total['card'] = total['total'] * 100
        purchase['total'] = total

        # Create description
        purchase['desc_item'] = items[0].item
        purchase['desc'] = str(items[0].quantity) + " " + items[0].item.name

        count = cart.count_products()
        if count > 1:
            purchase['desc'] = purchase['desc'] + ' and ' + str(count - 1) + ' more item(s).'

        # Add shipping address
        try:
            customer_address = Address.objects.get(user=self.customer_id, most_current=True)
        except Address.DoesNotExist:
            customer_address = None

        purchase['address'] = customer_address

        return purchase

    def get_address(self):
        address = Address.objects.filter(user=self.address_id)

        return address

    def items(self):
        return ShoppingCart.objects.get(id=self.cart_id).all()

    def shipping(self):
        try:
            return json.loads(self.shipping_object)
        except TypeError:
            return None

    def save(self, *args, **kwargs):
        """On save, update timestamps"""
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super().save(*args, **kwargs)

    def finalize(self):
        # finalize the various data fields we need to differentiate completed orders
        finalized_time = datetime.now()
        self.finalized = True
        self.date_finalized = finalized_time
        self.date_modified = finalized_time

        # move the items from the cart (temporary) to the order (permanent)
        for item in ShoppingCart.objects.get(self.cart_id).get_cart_items():
            self.items.add(item)

        # release the cart since we're done with it now
        self.cart = None

        self.save()

    def status(self):
        if self.finalized and self.shipping_tracking:
            return self.STATUS_CHOICES['Shipped']
        elif self.shipping() and self.payment:
            return self.STATUS_CHOICES['Ready to Ship']
        elif self.shipping() and self.address:
            return self.STATUS_CHOICES['Shipping Chosen']
        elif self.address:
            return self.STATUS_CHOICES['Addressed']
        else:
            return self.STATUS_CHOICES['Created']


class Address(models.Model):
    user = models.ForeignKey('auth.user')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=100, null=True)
    street_address1 = models.CharField(max_length=100)
    street_address2 = models.CharField(max_length=100, null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=2, null=True)
    zipcode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, null=True, default="US")
    phone = models.CharField(max_length=15, null=True)
    email = models.CharField(max_length=100, null=True)

    # Used to denote the most current address
    most_current = models.BooleanField(default=True)
