from django.shortcuts import render, redirect
from django.views.generic import FormView
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout
from django.contrib import messages
from django.urls import reverse_lazy
from django.views import View
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from .forms import UserRegistrationForm, UserUpdateForm


def profile_update_email(user, email_subject, email_template_name):
    if not user.email:
        return
    try:
        message = render_to_string(
            email_template_name,
            {
                "user": user,
                "email_subject": email_subject,
            },
        )
        send_email = EmailMultiAlternatives(email_subject, "", to=[user.email])
        send_email.attach_alternative(message, "text/html")
        send_email.send()
    except Exception:
        pass


class UserRegistrationView(FormView):
    template_name = "accounts/reg.html"
    form_class = UserRegistrationForm
    success_url = reverse_lazy("profile_update")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(
            self.request,
            f"Welcome to NexusBank, {user.first_name or user.username}! Your account #{user.account.account_no} is ready.",
        )
        return super().form_valid(form)


class UserLoginView(LoginView):
    template_name = "accounts/user_login.html"

    def get_success_url(self):
        messages.success(self.request, f"Welcome back, {self.request.user.first_name or self.request.user.username}!")
        return reverse_lazy("home")


class UserLogout(LogoutView):
    def get_success_url(self):
        if self.request.user.is_authenticated:
            logout(self.request)
        return reverse_lazy("home")


def userLogout(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been safely logged out.")
    return redirect("home")


class UserProfileUpdate(LoginRequiredMixin, View):
    template_name = "accounts/profile.html"
    title = "Profile & Account Settings"

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {"form": form, "title": self.title})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile information has been updated.")
            return redirect("profile_update")
        return render(request, self.template_name, {"form": form, "title": self.title})


class ChangePassword(LoginRequiredMixin, PasswordChangeView):
    template_name = "accounts/change_password.html"
    success_url = reverse_lazy("profile_update")

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Your password has been changed successfully.")
        profile_update_email(
            self.request.user,
            "Password Changed Successfully",
            "accounts/change_password_email.html",
        )
        return response
