from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("me/", views.MeView.as_view(), name="me"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("staff/", views.StaffListCreateView.as_view(), name="staff-list-create"),
    path("staff/<int:pk>/", views.StaffDetailView.as_view(), name="staff-detail"),
    path("citizens/", views.CitizenListView.as_view(), name="citizen-list"),
]
