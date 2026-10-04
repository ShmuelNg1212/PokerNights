from django.contrib.auth.forms import UserCreationForm

from .models import User


class SignupForm(UserCreationForm):
    """Django's sign-up rules with shorter words. The validators are unchanged."""

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["username"].help_text = "The name you log in with."
        self.fields["password1"].help_text = "At least 8 characters. Not a common password and not only digits."
        self.fields["password2"].label = "Repeat password"
        self.fields["password2"].help_text = ""

    def validate_password_for_user(self, user, password_field_name="password1"):
        # A broken rule is reported under Password, where the rule is stated. A mismatch stays under Repeat password.
        super().validate_password_for_user(user, "password1")
