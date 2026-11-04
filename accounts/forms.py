from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .constants import GENDER_TYPE, ACCOUNT_TYPE
from .models import UserAddress, UserBankAccount

INPUT_STYLE = (
    "appearance-none block w-full bg-slate-50 text-slate-800 "
    "border border-slate-300 rounded-xl py-3 px-4 leading-tight "
    "focus:outline-none focus:bg-white focus:border-indigo-600 focus:ring-2 focus:ring-indigo-100 transition"
)


class UserRegistrationForm(UserCreationForm):
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE)
    gender = forms.ChoiceField(choices=GENDER_TYPE)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=50)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "account_type",
            "birth_date",
            "gender",
            "street_address",
            "city",
            "postal_code",
            "country",
        ]

    def save(self, commit=True):
        created_user = super().save(commit=False)
        if commit:
            created_user.save()
            birth_date = self.cleaned_data.get("birth_date")
            account_type = self.cleaned_data.get("account_type")
            gender = self.cleaned_data.get("gender")
            city = self.cleaned_data.get("city")
            street_address = self.cleaned_data.get("street_address")
            postal_code = self.cleaned_data.get("postal_code")
            country = self.cleaned_data.get("country")

            UserAddress.objects.create(
                user=created_user,
                street_address=street_address,
                postal_code=postal_code,
                city=city,
                country=country,
            )

            UserBankAccount.objects.create(
                user=created_user,
                account_type=account_type,
                birth_date=birth_date,
                gender=gender,
                account_no=100000 + created_user.id,
            )
        return created_user

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": INPUT_STYLE})


class UserUpdateForm(forms.ModelForm):
    birth_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE)
    gender = forms.ChoiceField(choices=GENDER_TYPE)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=50)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=50)

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({"class": INPUT_STYLE})

        user_account = None
        user_address = None
        if self.instance and self.instance.pk:
            user_account = getattr(self.instance, "account", None)
            user_address = getattr(self.instance, "address", None)

        if user_account:
            self.fields["account_type"].initial = user_account.account_type
            self.fields["gender"].initial = user_account.gender
            self.fields["birth_date"].initial = user_account.birth_date
        if user_address:
            self.fields["street_address"].initial = user_address.street_address
            self.fields["city"].initial = user_address.city
            self.fields["postal_code"].initial = user_address.postal_code
            self.fields["country"].initial = user_address.country

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            user_account = getattr(user, "account", None)
            user_address = getattr(user, "address", None)

            if user_account:
                user_account.account_type = self.cleaned_data.get("account_type")
                user_account.gender = self.cleaned_data.get("gender")
                user_account.birth_date = self.cleaned_data.get("birth_date")
                user_account.save()

            if user_address:
                user_address.street_address = self.cleaned_data.get("street_address")
                user_address.city = self.cleaned_data.get("city")
                user_address.postal_code = self.cleaned_data.get("postal_code")
                user_address.country = self.cleaned_data.get("country")
                user_address.save()

        return user
