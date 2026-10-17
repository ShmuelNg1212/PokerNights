from django import forms
from django.contrib.auth.forms import AuthenticationForm, SetPasswordForm, UserCreationForm

from .models import User


def keyboard_hints(form):
    """The phone keyboard's return key says Next until the last field, then Go."""
    names = list(form.fields)
    for name in names:
        form.fields[name].widget.attrs["enterkeyhint"] = "go" if name == names[-1] else "next"


class LoginForm(AuthenticationForm):
    """Django's login check with one plain message that does not say which field was wrong."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "That username and password don't match. Check capital letters.",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        keyboard_hints(self)


class PlainWords:
    """The app's wording for Django's password and username errors, by error code.

    A code that is not listed keeps Django's message. The cursor goes to the first refused field.
    """

    WORDS = {
        "unique": "That name is taken. Try another.",
        "password_too_short": "Too short. Use at least 8 characters.",
        "password_too_common": "That password is too common. Pick a less usual one.",
        "password_entirely_numeric": "Use more than digits.",
        "password_too_similar": "Too close to your username. Pick something different.",
        "password_mismatch": "The two passwords don't match.",  # the profile's change form still has two
    }
    USERNAME_WORDS = {"invalid": "Use only letters, numbers and @ . + - _, with no spaces."}
    PASSWORD_HELP = "At least 8 characters, not a common password, not only digits, and not like your username."

    def full_clean(self):
        super().full_clean()
        if not self.is_bound or not self._errors:
            return
        for name, errors in list(self._errors.items()):
            words = {**self.WORDS, **(self.USERNAME_WORDS if name == "username" else {})}
            plain = [
                forms.ValidationError(words[error.code], code=error.code) if error.code in words else error
                for error in errors.as_data()
            ]
            self._errors[name] = type(errors)(
                plain, error_class=getattr(errors, "error_class", None), renderer=errors.renderer,
                field_id=getattr(errors, "field_id", None),
            )
        refused = next((name for name in self.fields if name in self._errors), None)
        if refused:
            for field in self.fields.values():
                field.widget.attrs.pop("autofocus", None)
            self.fields[refused].widget.attrs["autofocus"] = True


class SignupForm(PlainWords, UserCreationForm):
    """Django's sign-up rules with the app's words. The validators are unchanged."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "Your friends see this name. Letters, numbers and @ . + - _, no spaces."
        self.fields["password1"].help_text = self.PASSWORD_HELP
        # One password field: Show and the phone's password manager catch a typo. Without the
        # second field Django's mismatch check has nothing to compare and is skipped.
        del self.fields["password2"]
        keyboard_hints(self)

    def validate_password_for_user(self, user, password_field_name="password1"):
        # A broken rule is reported under Password, where the rule is stated.
        super().validate_password_for_user(user, "password1")


class PasswordPairForm(PlainWords, SetPasswordForm):
    """Django's set-password rules with a Repeat password field, worded as on Sign up."""

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["new_password1"].help_text = self.PASSWORD_HELP
        self.fields["new_password1"].widget.attrs["autofocus"] = True
        self.fields["new_password2"].label = "Repeat password"
        self.fields["new_password2"].help_text = ""
        keyboard_hints(self)

    def validate_password_for_user(self, user, password_field_name="new_password1"):
        super().validate_password_for_user(user, "new_password1")


class NewPasswordForm(PasswordPairForm):
    """The reset link's form: one password field, as on Sign up."""

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        del self.fields["new_password2"]
        keyboard_hints(self)  # again: new_password1 is now the last field, so its key says Go


class ChangePasswordForm(PasswordPairForm):
    """The new-password rules plus the current password. The service checks the current one, so a
    wrong one is counted; a form refused for its new password never tests the current one."""

    current_password = forms.CharField(
        label="Current password", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )

    field_order = ["current_password", "new_password1", "new_password2"]

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["new_password1"].label = "New password"
        self.fields["new_password1"].widget.attrs.pop("autofocus", None)  # it sits in a closed disclosure on the profile
        keyboard_hints(self)
