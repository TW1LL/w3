from io import BytesIO
import os

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.files.base import ContentFile
from django.contrib.staticfiles.templatetags.staticfiles import static
from w3.settings import MEDIA_ROOT
from PIL import Image


class Category(models.Model):

    name = models.CharField(max_length=255, default="New Product")
    description = models.TextField(default="Mechanical designs by w^3")
    on_hand = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    preview_image = models.ImageField(null=True, blank=True, upload_to="uploads")
    image1 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image2 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image3 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image4 = models.ImageField(null=True, blank=True, upload_to="uploads")
    image5 = models.ImageField(null=True, blank=True, upload_to="uploads")

    image_fields = [image1, image2, image3, image4, image5]

    cat_img = "cart/images/w3rect.png"
    plural_name = "Default Plural Name"
    preview_image_size = (125, 125)

    class Meta:
        abstract = True

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

    def preview_img(self):
        if self.preview_image:
            return [u'<img src="{}/{}" />'.format(MEDIA_ROOT, self.preview_image.url), ]
        else:
            return "No preview image"

    def image_list(self):
        images = []
        for img in [self.image1, self.image2, self.image3, self.image4, self.image5]:
            if img:
                images.append(u'<a href="{0}/{1}"><img src="{0}/{2}"/></a>'.format(MEDIA_ROOT, img.url,
                                                                                   img.url.replace(".jpg",
                                                                                                   "_preview.jpg")))
        if images:
            return images
        else:
            return "No image"

    def image(self):
        if self.preview_image:
            return "{}/{}".format(MEDIA_ROOT, self.preview_image.url)
        else:
            return static(self.cat_img)

    # allow the img files to be used in thumbnails/previews
    preview_img.short_description = "Thumb"
    preview_img.allow_tags = True

    image_list.short_description = "Thumb"
    image_list.allow_tags = True

    def save(self, *args, **kwargs):
        if self.image1:
            self.generate_preview_thumb()
        else:
            self.preview_image.delete(save=True)

        self.generate_img_thumbs()

        super().save(*args, **kwargs)

    def generate_preview_thumb(self):
        # special logic for the preview image because it's generated from image1
        # probably duplicative and should be removed
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
    # cat_img = "cart/watches/img.jpg"
    cat_description = "Sophisticated wristpieces that hold time."
    plural_name = "Watches"

    class Meta:
        verbose_name = "Watch Product"


class Paintball(Category):
    # cat_img = "cart/paintball/img.jpg"
    cat_description = "Sweet gats."
    plural_name = "Paintball Products"

    class Meta:
        verbose_name = "Paintball Product"


class ShoppingCart(models.Model):
    owner = models.ForeignKey('auth.user')
    item = models.ForeignKey(Watch, null=True)
    quantity = models.IntegerField(default=1)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.owner.username + "'s item - " + str(self.quantity)
