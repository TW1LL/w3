from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField('auth.user')
    address = models.TextField(default="")
    orders = models.CommaSeparatedIntegerField(max_length=255, null=True)

    def getName(self):
        return self.user.first_name + ' ' + self.user.last_name

    def __str__(self):
        return self.user.username