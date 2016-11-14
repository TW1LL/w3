from django.contrib import admin
from cart.models import Watch, Paintball, ShoppingCart

admin.site.register(Watch)
admin.site.register(ShoppingCart)

@admin.register(Paintball)
class PaintballAdmin(admin.ModelAdmin):
    list_display = ('preview_img',)

    fields = [
        'name',
        'description',
        'on_hand',
        'price',
        'image1',
        'image2',
        'image3',
        'image4',
        'image5',
        'image_list']
    readonly_fields = ['image_list',]