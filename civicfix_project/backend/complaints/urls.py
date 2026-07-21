from django.urls import path

from . import views

urlpatterns = [
    path("", views.ComplaintListCreateView.as_view(), name="complaint-list-create"),
    path("stats/", views.DashboardStatsView.as_view(), name="complaint-stats"),
    path("notifications/", views.NotificationListView.as_view(), name="notification-list"),
    path("notifications/<int:pk>/read/", views.NotificationMarkReadView.as_view(), name="notification-read"),
    path("<int:pk>/", views.ComplaintDetailView.as_view(), name="complaint-detail"),
    path("<int:pk>/status/", views.ComplaintStatusUpdateView.as_view(), name="complaint-status-update"),
    path("<int:pk>/updates/", views.ComplaintUpdateListCreateView.as_view(), name="complaint-updates"),
]
