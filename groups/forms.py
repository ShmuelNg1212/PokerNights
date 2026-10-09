from django import forms


class NameForm(forms.Form):
    name = forms.CharField(label="Name", max_length=60)


class GroupForm(NameForm):
    name = forms.CharField(label="Group name", max_length=60)


class MemberForm(NameForm):
    """A host's form for another member: the name, and a note only hosts see."""

    contact = forms.CharField(label="Contact (optional)", max_length=120, required=False,
                              help_text="A phone number or a note. Only hosts see it.")


class NamesForm(forms.Form):
    names = forms.CharField(
        label="Names", widget=forms.Textarea(attrs={"rows": 4, "autocapitalize": "words", "autocomplete": "off", "spellcheck": "false"}),
        help_text="One name per line, up to 30. They join the roster without a login.",
    )
