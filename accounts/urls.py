from django.urls import path
from . import views

urlpatterns = [
    path("user_registration/", views.UserRegistrationView.as_view(), name="registration"),
    path("login/", views.UserLoginView.as_view(), name="login"),
    path("logout/", views.userLogout, name="logout"),
    path("profile/", views.UserProfileUpdate.as_view(), name="profile_update"),
    path("profile/", views.UserProfileUpdate.as_view(), name="profile"),
    path("change_password/", views.ChangePassword.as_view(), name="change_password"),
]
