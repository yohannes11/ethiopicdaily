from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    # Public
    path("", views.homepage, name="homepage"),
    path("article/<slug:slug>/", views.article_detail, name="article_detail"),
    path("article/<slug:slug>/react/", views.react_to_article, name="react_to_article"),

    # Editorial — writers + admins
    path("editorial/", views.editorial_dashboard, name="editorial_dashboard"),
    path("editorial/new/", views.article_create, name="article_create"),
    path("editorial/<slug:slug>/edit/", views.article_edit, name="article_edit"),
    path("editorial/<slug:slug>/submit/", views.article_submit, name="article_submit"),
    path("editorial/<slug:slug>/withdraw/", views.article_withdraw, name="article_withdraw"),
    path("editorial/<slug:slug>/delete/", views.article_delete, name="article_delete"),
    path("editorial/<slug:slug>/preview/", views.article_preview, name="article_preview"),

    # Review — reviewers + admins
    path("review/", views.review_queue, name="review_queue"),
    path("review/<slug:slug>/", views.review_article, name="review_article"),
    path("review/<slug:slug>/action/", views.review_action, name="review_action"),
]
