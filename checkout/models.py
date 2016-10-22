from django.db import models
from django.utils import timezone
from decimal import Decimal
import json


# Create your models here.
class Order(models.Model):
    STATUS_CHOICES = (
        ('DONE', 'Order Complete'),
        ('SHIPPED', 'Order Shipping'),
        ('CREATED', 'Order created, but not continued'),
        ('CRESHIP', 'Order created, Ship Address completed'),
        ('CRESHME', 'Order created, Ship method chosen'),
        ('CREPAID', 'Order Created, Payment Processed'),
        ('CHEKOUT', 'Order finalized, and order successfully placed.'),

    )

    customer = models.ForeignKey('account.UserProfile', null=True)
    cart = models.ManyToManyField('cart.ShoppingCart')
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='CREATED')
    shipping_object = models.TextField(default=None, null=True)
    payment = models.CharField(null=True, max_length=255, default="None")

    # Creates purchase object
    def info(self):
        total = {'sub': 0, 'shipping': 0, 'total': 0}
        purchase = {'total_qty': 0}
        items = self.cart.all()
        count = 0
        # Get total of things in the cart.
        for product in items:
            count += 1
            total['sub'] += product.quantity * product.item.price
            purchase['total_qty'] += product.quantity

        # Add shipping cost
        purchase['qty'] = count
        if self.shipping_object == None:
            total['shipping'] = 0
        else:
            shipping = json.loads(self.shipping_object)
            total['shipping'] = Decimal(shipping['rate'])
        # grand total
        total['total'] = total['sub'] + total['shipping']
        total['card'] = total['total'] * 100

        purchase['total'] = total

        # Create description
        purchase['desc_item'] = items[0].item
        purchase['desc'] = str(items[0].quantity) + " " + items[0].item.name
        if count > 1:
            purchase['desc'] = purchase['desc'] + ' and ' + str(count - 1) + ' more item(s).'
        # Add shipping address
        if self.customer != None:
            if self.customer.getName() == None:
                purchase['address'] = "\n"
            else:
                purchase['address'] = self.customer.getName() + "\n"
            if self.customer.address == None:
                pass
            else:
                purchase['address'] += self.customer.address
        else:
            purchase['address'] = ""

        return purchase

    def address(self):
        address = self.customer.address.split('\n')
        name = self.customer.getName()
        return [name, '', address[0], address[1].split(', ')[0], address[1].split(', ')[1], address[2]]

    def items(self):
        return self.cart.all()


class FinalOrder(models.Model):
    STATUS_CHOICES = (
        ('DONE', 'Order Complete'),
        ('SHIPPED', 'Order Shipping'),
        ('CREATED', 'Order created, but not continued'),
        ('CRESHIP', 'Order created, Ship Address completed'),
        ('CRESHME', 'Order created, Ship method chosen'),
        ('CREPAID', 'Order Created, Payment Processed'),
        ('CHEKOUT', 'Order finalized, and order successfully placed.'),

    )

    created = models.DateTimeField(editable=False)
    modified = models.DateTimeField()
    customer = models.ForeignKey('account.UserProfile', null=True)

    items = models.ManyToManyField('cart.Watch')
    desc = models.CharField(max_length=255, default="1 Watch")
    status = models.CharField(max_length=7, choices=STATUS_CHOICES, default='CHEKOUT')
    payment = models.CharField(null=True, max_length=255, default="None")
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    shipping_address = models.TextField(default="")
    shipping_object = models.TextField(default="")
    shipping_label = models.TextField(default="None")
    shipping_tracking = models.TextField(default="None")

    def shipping(self):
        return json.loads(self.shipping_object)

    def save(self, *args, **kwargs):
        ''' On save, update timestamps '''
        if not self.id:
            self.created = timezone.now()
        self.modified = timezone.now()
        return super(FinalOrder, self).save(*args, **kwargs)