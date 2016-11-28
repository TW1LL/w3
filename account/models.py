from django.db import models

from checkout.models import Address


class CustomerProfile(models.Model):
    customer = models.OneToOneField('auth.user')
    address = models.OneToOneField(Address, null=True, default=None)
    active = models.BooleanField(default=True)

    def get_full_name(self):
        return self.customer.first_name + ' ' + self.customer.last_name

    def __str__(self):
        return self.customer.username
