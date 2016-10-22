from django import forms
from django.contrib.auth.models import User
from account.models import UserProfile
from django.utils.translation import ugettext_lazy as _
from localflavor.us.forms import USStateField, USZipCodeField


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
        
class UserProfileForm(forms.Form):
    pk = forms.CharField(widget=forms.HiddenInput())
    first_name = forms.CharField(label=("First Name"), widget=forms.TextInput)
    last_name = forms.CharField(label=("Last Name"), widget=forms.TextInput)
    street_address = forms.CharField(label=("Street Address"), widget=forms.TextInput)
    city = forms.CharField(label=("City"), widget=forms.TextInput)
    state = USStateField()
    zipcode = USZipCodeField()
    
    def save(self):
        address = self.cleaned_data["street_address"] + "\n" + self.cleaned_data["city"] + ", " + self.cleaned_data["state"] + "\n" + self.cleaned_data["zipcode"]
        userprof = UserProfile.objects.get(pk=self.cleaned_data["pk"])
        userprof.address = address
        userprof.save()
        User.objects.filter(pk=userprof.user.id).update(first_name = self.cleaned_data['first_name'], last_name = self.cleaned_data['last_name'])
