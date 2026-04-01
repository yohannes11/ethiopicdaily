from django import forms
from .models import User


class CreateUserForm(forms.Form):
    first_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Abebe'}),
    )
    last_name = forms.CharField(
        max_length=150, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Girma'}),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'user@example.com'}),
    )
    role = forms.ChoiceField(choices=User.Role.choices)
    send_email = forms.BooleanField(required=False, initial=True)

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_role(self):
        role = self.cleaned_data.get('role', '')
        if role not in User.Role.values:
            raise forms.ValidationError("Invalid role selected.")
        return role
