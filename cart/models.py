from io import BytesIO
import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.contrib.staticfiles.templatetags.staticfiles import static
from w3.settings import MEDIA_ROOT
from PIL import Image


class Category(models.Model):
    # ToDo: Refactor out the "plural_name" attribute - use .__meta__.plural_name
    """
    Base class for all item categories in the store.
    To implement a subclass, you should make sure you override the following attributes:
    category_name
    cat_img
    plural_name
    """

    category_name = "Category"

    name = models.CharField(max_length=255, default="New Product")
    description = models.TextField(default="Mechanical designs by w^3")
    on_hand = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    # important information for shipping
    sizes = (
        ("FlatRateEnvelope", "Flat Rate Envelope (12.5 x 9.5)"),
        ("FlatRatePaddedEnvelope", "Flat Rate Envelope Padded (12.5 x 9.5)"),
        ("SmallFlatRateBox", "Flat Rate Small Box (8.6 x 5.3 x 1.6)"),
        ("MediumFlatRateBox1", 'Flat Rate Medium Box 1 (11 x 8.5 x 5.5)'),
        ("MediumFlatRateBox2", 'Flat Rate Medium Box 2 (13.6 x 11.8 x 5.5)'),
        ("LargeFlatRateBox", 'Flat Rate Large Box (12 x 12 x 5.5)'),
        ("LargeFlatRateBoardGameBox", 'Flat Rate Board Game Box (23.6 x 11.75 x 3)'),
        ("custom", 'Fill out the custom size below')
    )

    packaging = models.CharField(max_length=100, choices=sizes, null=False, help_text="Size listed is internal inches")
    weight = models.IntegerField(help_text="Item's weight in oz")
    custom_width = models.IntegerField(help_text="Exterior box size in inches", null=True, blank=True)
    custom_height = models.IntegerField(help_text="Exterior box size in inches", null=True, blank=True)
    custom_depth = models.IntegerField(help_text="Exterior box size in inches", null=True, blank=True)

    preview_image = models.ImageField(null=True, blank=True, upload_to="uploads")

    # If you make changes here, make sure to make equivalent changes to the lists in:
    # image_urls() - seen in the store
    # admin_image_list() and generate_img_thumbs() - seen on the admin pages
    image1 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image2 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image3 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image4 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image5 = models.ImageField(null=True, blank=True, upload_to="uploads")

    # default image for categories, should be overridden when subclassing
    cat_img = "cart/images/w3rect.png"
    plural_name = "Default Plural Name"

    # default thumbnail size
    preview_image_size = (125, 125)

    def update_on_hand(self, amount):
        self.on_hand = self.on_hand + amount

    def __str__(self):
        return self.name

    @staticmethod
    def get_categories():
        categories = []
        for cls in Category.__subclasses__():
            categories.append({"name": cls.__name__, "image": cls.cat_img, "description": cls.cat_description,
                               "plural_name": cls.plural_name, })
        return categories

    def get_preview_image(self):
        if self.preview_image:
            return [u'<img src="{}" />'.format(self.preview_image.url), ]
        else:
            return "No preview image"

    def admin_image_list(self):
        images = []
        for img in [self.image1, self.image2, self.image3, self.image4, self.image5]:
            if img:
                images.append(u'<a href="{}"><img src="{}"/></a>'.format(
                    img.url, img.url.replace(".jpg", "_preview.jpg")))
        if images:
            return images
        else:
            return "No image"

    def image_urls(self):
        # this provides images for the store page views
        images = []
        for img in [self.image1, self.image2, self.image3, self.image4, self.image5]:
            if img:
                images.append(img.url)
        if images:
            return images
        else:
            return None

    def image(self):
        if self.image1:
            return self.image1.url
        else:
            return static(self.cat_img)

    # allow the img files to be used in thumbnails/previews
    get_preview_image.short_description = "Thumb"
    get_preview_image.allow_tags = True

    admin_image_list.short_description = "Thumb"
    admin_image_list.allow_tags = True

    def save(self, *args, **kwargs):
        if self.image1:
            self.generate_preview_thumb()
        else:
            self.preview_image.delete(save=True)

        self.generate_img_thumbs()

        super().save(*args, **kwargs)

    def generate_preview_thumb(self):
        # special logic for the preview image because it's generated from image1
        pil_image = Image.open(self.image1)
        pil_image = pil_image.resize(self.get_thumb_size(pil_image.size))

        new_img_io = BytesIO()
        name = self.image1.name.replace(".jpg", "_preview.jpg")
        pil_image.save(new_img_io, format="JPEG")

        self.preview_image.delete(save=False)
        self.preview_image.save(
            name,
            content=ContentFile(new_img_io.getvalue()),
            save=False
        )

    def generate_img_thumbs(self):
        images = [self.image2, self.image3, self.image4, self.image5]

        for img in images:
            if img and not os.path.isfile(os.path.join(MEDIA_ROOT, img.name)):
                pil_image = Image.open(img)
                pil_image = pil_image.resize(self.get_thumb_size(pil_image.size))

                name = img.name.replace(".jpg", "_preview.jpg")
                pil_image.save(os.path.join(MEDIA_ROOT, 'uploads', name), format="JPEG")

    def get_thumb_size(self, image_size):
        desired_x, desired_y = self.preview_image_size
        x, y = image_size
        if x > desired_x or y > desired_y:
            return self.get_thumb_size((x//2, y//2))
        else:
            return x, y


class Part(models.Model):
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255, null=True)
    on_hand = models.IntegerField()
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def update_on_hand(self, amount):
        self.on_hand = self.on_hand + amount

    def __str__(self):
        return self.name

    class Meta:
        abstract = True


class Watch(Category):
    cat_img = "cart/watches/img.jpg"
    cat_description = "Sophisticated wristpieces that hold time."
    plural_name = "Watches"

    class Meta:
        verbose_name = "Watch"
        verbose_name_plural = "Watches"


class Paintball(Category):
    cat_img = "cart/paintball/img.jpg"
    cat_description = "Sweet gats."
    plural_name = "Paintball Products"

    class Meta:
        verbose_name = "Paintball"
        verbose_name_plural = "Paintball Products"


class ShoppingCart(models.Model):
    customer = models.ForeignKey('auth.user')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.customer.username + "'s cart"

    def count_items(self):
        count = 0
        for item in CartItem.objects.filter(cart=self.id).all():
            count += item.quantity
        return count

    def count_products(self):
        return len(CartItem.objects.filter(cart=self.id).all())

    def total_price(self):
        value = 0
        for item in CartItem.objects.filter(cart=self.id).all():
            value += item.get_price() * item.get_quantity()
        return value

    def get_cart_items(self):
        return list(CartItem.objects.filter(cart=self.id).all())


class CartItem(models.Model):
    # a wrapper for the item class to allow tracking quantity of a given item in the cart
    quantity = models.IntegerField(default=1)
    cart = models.ForeignKey(ShoppingCart)
    item = models.ForeignKey(Category)

    def change_quantity(self, count=1):
        self.quantity += count

        print(self.quantity)
        if self.quantity < 1:
            print("deleting")
            self.delete()
        else:
            self.save()

    def get_price(self):
        return self.item.price

    def get_quantity(self):
        return self.quantity

    def image(self):
        return self.item.image()

    def name(self):
        return self.item.name

    def on_hand(self):
        return self.item.on_hand

    def price(self):
        return self.item.price

    def subtotal(self):
        return self.item.price * self.quantity

    def category(self):
        print(self.item.__dict__)
        return ''
