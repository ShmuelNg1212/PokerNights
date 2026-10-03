from django.contrib.auth import login
from django.contrib.auth.decorators import login_not_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import SignupForm


def safe_next(request, default="home"):
    """The ``next`` target if it stays on this site, else ``default``."""
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}):
        return target
    return default


@login_not_required
def signup(request):
    if request.user.is_authenticated:
        return redirect(safe_next(request))
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(safe_next(request))
    return render(request, "accounts/signup.html", {"form": form, "next": safe_next(request, "")})
