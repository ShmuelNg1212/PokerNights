from django import forms


class NameForm(forms.Form):
    name = forms.CharField(label="Name", max_length=60)


class GroupForm(NameForm):
    name = forms.CharField(label="Group name", max_length=60)
