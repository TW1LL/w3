from django import forms
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from localflavor.us.forms import USStateField, USZipCodeField, USPhoneNumberField

from account.models import CustomerProfile, Address
from cart.models import ShoppingCart
from checkout.models import Order


class RegistrationForm(forms.ModelForm):
    """
    A form that creates a user, with no privileges, from the given username and
    password.
    """
    error_messages = {
        'password_mismatch': _("The two password fields didn't match."),
    }
    password1 = forms.CharField(label=_("Password"),
        widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Password confirmation"),
        widget=forms.PasswordInput,
        help_text=_("Enter the same password as above, for verification."))
    email = forms.CharField(label=_("Email"),widget=forms.TextInput)
    
    class Meta:
        model = User
        fields = ("username","first_name","last_name")

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                self.error_messages['password_mismatch'],
                code='password_mismatch',
            )
        return password2

    def save(self, commit=True):
        user = super(RegistrationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class AddressForm(forms.Form):
    first_name = forms.CharField(label="First Name", widget=forms.TextInput)
    last_name = forms.CharField(label="Last Name", widget=forms.TextInput)
    company_name = forms.CharField(label="Company Name", widget=forms.TextInput, required=False)
    street_address1 = forms.CharField(label="Street Address", widget=forms.TextInput)
    street_address2 = forms.CharField(label="Street Address Continued", widget=forms.TextInput, required=False)
    city = forms.CharField(label="City", widget=forms.TextInput)
    state = USStateField()
    zipcode = USZipCodeField()
    country = forms.CharField(label="Country", widget=forms.TextInput, required=False)
    phone = USPhoneNumberField()
    email = forms.CharField(label="Email", widget=forms.TextInput)

    class Meta:
        model = Address
        exclude = ["customer"]

    def save(self):
        customer_profile, created = CustomerProfile.objects.get_or_create(customer=self.user)
        user_cart = ShoppingCart.objects.get(customer=self.user)
        order = Order.objects.get(cart=user_cart)

        address_is_new = self.duplicates_existing_address(self.cleaned_data)

        if address_is_new:
            # make sure the old address isn't pulled as most recent
            if customer_profile.address:
                customer_profile.address.most_current = False
                customer_profile.address.save()

            address = Address.objects.create(
                customer=User.objects.get(id=self.user),
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                company_name=self.cleaned_data["company_name"],
                street_address1=self.cleaned_data["street_address1"],
                street_address2=self.cleaned_data["street_address2"],
                city=self.cleaned_data["city"],
                state=self.cleaned_data["state"],
                zipcode=self.cleaned_data["zipcode"],
                country=self.cleaned_data["country"],
                phone=self.cleaned_data["phone"],
                email=self.cleaned_data["email"]
            )

            address.save()
            order.address = address
            order.save()

            customer_profile.address = address
            customer_profile.save()

            User.objects.filter(pk=customer_profile.customer_id).update(first_name=self.cleaned_data['first_name'],
                                                                        last_name=self.cleaned_data['last_name'])

    def duplicates_existing_address(self, new_address):
        """
        Determines whether a dict of address data matches any existing addresses for this user.
        :param new_address: dict of new address data
        :return: boolean of whether address matches an existing address
        """

        addresses = Address.objects.filter(customer=self.user)

        for address in addresses:
            match = True
            for field in self.cleaned_data:
                value = self.cleaned_data[field]
                address_value = getattr(address, field)
                if value != address_value:
                    match = False
                    break
            if match:
                self.set_most_current_address(address)
                return False

        else:
            return True

    @staticmethod
    def set_most_current_address(address):
        order = Order.objects.get(customer=address.customer_id, finalized=False)

        current_address = Address.objects.get(customer=order.customer_id, most_current=True)
        current_address.most_current = False
        current_address.save()

        address.most_current = True
        address.save()

        order.address = address
        order.save()
