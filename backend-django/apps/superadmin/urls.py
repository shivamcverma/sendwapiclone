from django.urls import path
from . import views


app_name = "superadmin"


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "users/",
        views.users,
        name="users"
    ),

    path(
        "users/<int:user_id>/",
        views.user_detail,
        name="user_detail"
    ),

    path(
        "subscriptions/",
        views.subscriptions,
        name="subscriptions"
    ),

    path(
        "subscriptions/<int:plan_id>/edit/",
        views.edit_plan,
        name="edit_plan"
    ),

    path(
        "subscriptions/<int:plan_id>/delete/",
        views.delete_plan,
        name="delete_plan"
    ),

    path(
        "history/",
        views.history,
        name="history"
    ),

]