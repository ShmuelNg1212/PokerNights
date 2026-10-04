from django.contrib.auth import login
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from . import signup as signup_gate
from .forms import LoginForm, SignupForm


def safe_next(request, default="home"):
    """The ``next`` target if it stays on this site, else ``default``."""
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return target
    return default


class Login(auth_views.LoginView):
    """Django's login, with the name of the inviting group when the person came from an invite link."""

    form_class = LoginForm

    def form_invalid(self, form):
        # The username is kept, so the cursor goes to the field that came back empty.
        form.fields["username"].widget.attrs.pop("autofocus", None)
        form.fields["password"].widget.attrs["autofocus"] = True
        for field in form.fields.values():
            field.widget.attrs.update({"aria-invalid": "true", "aria-describedby": "login-error"})
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        target = safe_next(self.request, "")
        context["invited_to"] = signup_gate.invited_to(self.request, target)
        # Where sign-up needs an invite, the link is offered only when this visit carries one.
        context["can_sign_up"] = signup_gate.allowed(self.request, target)
        return context


@login_not_required
def signup(request):
    if request.user.is_authenticated:
        return redirect(safe_next(request))
    if not signup_gate.allowed(request, safe_next(request, "")):
        return render(request, "accounts/signup_closed.html", status=403)
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(signup_gate.after_signup(request, user, safe_next(request, "")) or safe_next(request))
    target = safe_next(request, "")
    context = {"form": form, "next": target, "invited_to": signup_gate.invited_to(request, target)}
    return render(request, "accounts/signup.html", context)
