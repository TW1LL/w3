import pickle
from datetime import datetime, date, timedelta
from re import finditer
import threading
from decimal import Decimal

from django.db import models
from django.utils import timezone

import easypost

from cart.models import Category, ShoppingCart, CartItem, Paintball, Watch


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
        "Complete": 'Order Complete',  # this isn't used because we currently don't confirm delivery
    }

    customer = models.ForeignKey('auth.User')
    cart = models.OneToOneField(ShoppingCart, null=True)
    address = models.ForeignKey('checkout.Address', null=True)
    payment = models.CharField(null=True, max_length=255, default="None")

    date_created = models.DateTimeField(editable=False)
    date_modified = models.DateTimeField()

    finalized = models.BooleanField(default=False)
    date_finalized = models.DateTimeField(null=True)

    items = models.ManyToManyField(CartItem)
    desc = models.CharField(max_length=255, default="1 Order")
    total = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    shipping_label = models.TextField(default="None")
    shipping_tracking = models.TextField(default="None")

    def __str__(self):
        return "Order for {}".format(self.customer.get_full_name())

    class Meta:
        verbose_name = "Customer Order"
        verbose_name_plural = "Customer Orders"

    def purchase_info(self):
        """
        Create purchase object
        :return:
        """
        cart = ShoppingCart.objects.get(id=self.cart_id)
        items = cart.get_cart_items()
        item_cost = cart.total_price()
        shipping_cost = self.get_shipping_cost()

        total = {
            'sub': item_cost,
            'shipping': shipping_cost,
            'total': item_cost + shipping_cost,
            'card': (item_cost + shipping_cost) * 100
        }

        purchase = {
            'total_qty': 0,
            'qty': cart.count_items(),
            'address': "",
            'desc_item': items[0].item,
            'desc': str(items[0].quantity) + " " + items[0].item.name,
            'total': total
        }

        count = cart.count_products()
        if count > 1:
            purchase['desc'] = purchase['desc'] + ' and ' + str(count - 1) + ' more item(s).'

        # Add shipping address
        try:
            address = Address.objects.get(customer=self.customer_id, most_current=True)
            customer_address = address.format_for_display()
        except Address.DoesNotExist:
            customer_address = None

        purchase['address'] = customer_address

        return purchase

    def get_address(self):
        address = Address.objects.get(id=self.address_id)

        return address

    def items(self):
        return ShoppingCart.objects.get(id=self.cart_id).all()

    def get_shipment(self):
        try:
            return Shipment.objects.get(order=self.id)
        except Shipment.DoesNotExist:
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
        elif self.get_shipping_cost() > 0 and self.payment != 'None':
            return self.STATUS_CHOICES['Ready to Ship']
        elif self.get_shipping_cost() > 0 and self.address:
            return self.STATUS_CHOICES['Shipping Chosen']
        elif self.address:
            return self.STATUS_CHOICES['Addressed']
        else:
            return self.STATUS_CHOICES['Created']

    def get_shipping_cost(self):
        try:
            shipment = Shipment.objects.get(order=self)
            return shipment.total_cost
        except Shipment.DoesNotExist:
            return 0


class Address(models.Model):
    customer = models.ForeignKey('auth.user')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=100, null=True, blank=True)
    street_address1 = models.CharField(max_length=100)
    street_address2 = models.CharField(max_length=100, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=2, null=True, blank=True)
    zipcode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, null=True, blank=True, default="United States")
    phone = models.CharField(max_length=15, null=True, blank=True)
    email = models.CharField(max_length=100, null=True, blank=True)

    # Used to denote the most current address
    most_current = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Customer Address"
        verbose_name_plural = "Customer Addresses"

    def __str__(self):
        return "Address for {}".format(self.customer.get_full_name())

    def format_for_display(self):
        if self.company_name and self.street_address2:
            address = """{}
                         ATTN: {} {}
                         {}
                         {}
                         {} {} {}""".format(self.company_name,
                                            self.first_name, self.last_name,
                                            self.street_address1,
                                            self.street_address2,
                                            self.city, self.state, self.zipcode)
        elif self.company_name:
            address = """{}
                         ATTN: {} {}
                         {}
                         {} {} {}""".format(self.company_name,
                                            self.first_name, self.last_name,
                                            self.street_address1,
                                            self.city, self.state, self.zipcode)
        elif self.street_address2:
            address = """{} {}
                         {}
                         {}
                         {} {} {}""".format(self.first_name, self.last_name,
                                            self.street_address1,
                                            self.street_address2,
                                            self.city, self.state, self.zipcode)

        else:
            address = """{} {}
                         {}
                         {} {} {}""".format(self.first_name, self.last_name,
                                            self.street_address1,
                                            self.city, self.state, self.zipcode)

        return address


class Shipment(models.Model):
    """
    A single order's shipment information
    """

    # shipments field holds flattened dictionary for all the shipment objects in the order
    shipments = models.BinaryField(null=True, blank=True)
    order = models.ForeignKey(Order)
    bought = models.BooleanField(default=False)
    total_cost = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)

    box_sizes = {
        "FlatRateEnvelope": [12.5, 9.5, 1],
        "FlatRatePaddedEnvelope": [12.5, 9.5, 1],
        "SmallFlatRateBox": [8.7, 5.4, 1.7],
        "MediumFlatRateBox1": [11, 8.5, 5.5],
        "MediumFlatRateBox2": [13.7, 11.9, 3.4],
        "LargeFlatRateBox": [12, 12, 5.5],
        "LargeFlatRateBoardGameBox": [23.7, 11.8, 3],
    }

    def __str__(self):
        return "Shipment for {}, Order #{}".format(self.order.customer.get_full_name(), self.order_id)

    def create_shipments(self):
        """
        Creates shipments for the entire order. Each item is setup to ship separately right now,
        so this generates a shipment for every item in the order
        To get results, call self.get_shipment()
        """

        shipments = {}
        shipment_threads = {}
        for cart_item in self.order.cart.get_cart_items():
            # deal with quantities here as well
            for i in range(cart_item.quantity):
                item = cart_item.item
                unique_identifier = "{} {} {} {}".format(self._identify_item_type(item), item.id, id(item), i)

                shipment_threads[unique_identifier] = threading.Thread(target=self.create_shipment,
                                                                       args=(item, shipments, unique_identifier))

        for thread in shipment_threads:
            shipment_threads[thread].start()
        for thread in shipment_threads:
            shipment_threads[thread].join()

        self.save_shipments(shipments)

    @staticmethod
    def _identify_item_type(item):
        """
        Workaround for the way django identifies classes for models.
        :param item:
        :return: string name of item type
        """
        # ToDo: Fix this to use a list that can be easily updated for new product categories
        try:
            if item.paintball:
                return "Paintball"
        except KeyError:
            pass

        try:
            if item.watch:
                return "Watch"
        except KeyError:
            pass

        raise RuntimeError("""Couldn't identify item type.
                           Have you added a case for your category to shipment._identify_item_type?""")

    def create_shipment(self, item, target_dict, id):
        """
        Create a shipment with the connected address and given item
        :param item: An item from this cart
        :return: Dictionary with shipment information
        """

        from_address = easypost.Address.create(
            company='Wagner Co.',
            street1='12 Hawk Drive',
            city='West Windsor',
            state='NJ',
            zip='08550',
            phone='609-468-0142'
        )

        to_address = easypost.Address.create(
            name="{} {}".format(self.order.address.first_name, self.order.address.last_name),
            company=self.order.address.company_name,
            street1=self.order.address.street_address1,
            street2=self.order.address.street_address2,
            city=self.order.address.city,
            state=self.order.address.state,
            zip=self.order.address.zipcode,
        )

        custom_size = self.box_sizes[item.packaging]

        if item.packaging == "custom":
            # setup a custom package size here
            custom_parcel = easypost.Parcel.create(
                length=custom_size[0],
                width=custom_size[1],
                height=custom_size[2],
                weight=item.weight
            )
        else:
            custom_parcel = easypost.Parcel.create(
                length=custom_size[0],
                width=custom_size[1],
                height=custom_size[2],
                weight=item.weight
            )
            if "MediumFlatRateBox" in item.packaging:
                # do something for the MFR boxes
                pass
            else:
                pass
                # do something for all other predefined USPS parcels
                usps_parcel = easypost.Parcel.create(
                    predefined_package=item.packaging,
                    weight=item.weight
                )

        shipment = easypost.Shipment.create(
            to_address=to_address,
            from_address=from_address,
            parcel=custom_parcel
        )

        target_dict[id] = shipment

    def view_rates(self):
        """
        returns a list of rates by item in the shipment
        :return:
        """
        rates = []
        shipments = self.get_shipments()
        for key in shipments:
            shipment = shipments[key]

            category, db_id, item_id, item_count = key.split(' ')

            if category == 'Paintball':
                item = Paintball.objects.get(id=db_id)
            elif category == 'Watch':
                item = Watch.objects.get(id=db_id)
            else:
                raise RuntimeError("""Could not find the model to retrieve item for shipping display.
                                      Have you added a case for your category?""")

            shipment_vars = {
                "item": item,
                "item_name": item.name,
                "item_image": item.preview_image.url,
                "key": key,
                "rates": []
            }

            for rate in shipment.rates:
                shipment_vars["rates"].append({
                    "rate_id": rate.id,
                    "carrier": rate.carrier,
                    "service": self._pascal_case_split(rate.service),
                    "rate": rate.rate,
                    "est_delivery_date": self._generate_delivery_date(None, rate.est_delivery_days),
                })

            rates.append(shipment_vars)
        return rates

    @staticmethod
    def _pascal_case_split(string):
        matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', string)
        return ' '.join([m.group(0) for m in matches])

    @staticmethod
    def _generate_delivery_date(item, est_delivery_days):
        """
        identifies the delivery date for an item by combining delivery time with any necessary production time with a
        default of 1 day handling time
        :param item: item id or object
        :param est_delivery_days: int
        :return: string delivery date
        """
        if est_delivery_days:
            return date.today() + timedelta(est_delivery_days)
        else:
            return "Delivery Date cannot be calculated"

    def buy(self):
        # shipment = json.loads(shipment)
        # self.shipments = easypost.Shipment.retrieve(shipment['shipment_id'])
        # self.shipments.buy(rate={'id': shipment['id']})
        # self.bought = True
        # self.save()
        # return [self.shipments.postage_label.label_url, self.shipments.tracking_code]
        raise ValueError("Fix this shit", self)

    def save_shipments(self, shipments):
        """
        takes dict of shipment objects and saves them as a byte string
        :param shipments: a dict of shipment objects, with their corresponding item id
        :return:
        """
        if self.order.finalized:
            raise PermissionError("Cannot change shipment information on a finalized shipment.")

        self.shipments = pickle.dumps(shipments)
        self.save()

    def get_shipments(self):
        return pickle.loads(self.shipments)

    def set_total_cost(self):
        shipments = self.get_shipments()
        total_cost = 0
        for key in shipments:
            shipment = shipments[key]
            shipment_price = Decimal(shipment.rate)
            total_cost += shipment_price
        self.total_cost = total_cost
        self.save()
