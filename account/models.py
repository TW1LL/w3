from django.db import models
from django.core.validators import validate_comma_separated_integer_list

from checkout.models import Address


class UserProfile(models.Model):
    user = models.OneToOneField('auth.user')
    address = models.OneToOneField(Address, null=True)
    orders = models.CharField(max_length=255, null=True,
                              validators=[validate_comma_separated_integer_list])
    active = models.BooleanField(default=True)

    def get_full_name(self):
        return self.user.first_name + ' ' + self.user.last_name

    def __str__(self):
        return self.user.username
