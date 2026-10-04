from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class LoginForm(AuthenticationForm):
    """Django's login check with one plain message that does not say which field was wrong."""

    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "That username and password don't match. Check capital letters.",
    }


class SignupForm(UserCreationForm):
    """Django's sign-up rules with the app's words. The validators are unchanged."""

    # Plain wording by Django's error code. A code that is not listed keeps Django's message.
    WORDS = {
        "unique": "That name is taken. Try another.",
        "password_too_short": "Too short. Use at least 8 characters.",
        "password_too_common": "That password is too common. Pick a less usual one.",
        "password_entirely_numeric": "Use more than digits.",
        "password_too_similar": "Too close to your username. Pick something different.",
        "password_mismatch": "The two passwords don't match.",
    }
    USERNAME_WORDS = {"invalid": "Use letters and numbers, with no spaces."}

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "Your friends see this name. Letters and numbers, no spaces."
        self.fields["password1"].help_text = (
            "At least 8 characters, not a common password, not only digits, and not like your username."
        )
        self.fields["password2"].label = "Repeat password"
        self.fields["password2"].help_text = ""

    def validate_password_for_user(self, user, password_field_name="password1"):
        # A broken rule is reported under Password, where the rule is stated. A mismatch stays under Repeat password.
        super().validate_password_for_user(user, "password1")

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
        # The cursor goes to the first refused field instead of always to Username.
        refused = next((name for name in self.fields if name in self._errors), None)
        if refused:
            self.fields["username"].widget.attrs.pop("autofocus", None)
            self.fields[refused].widget.attrs["autofocus"] = True
