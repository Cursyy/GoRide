from django.urls import path
from . import views

app_name = "reviews"

urlpatterns = [
    path('submit/', views.submit_review, name='submit_review'),
    path('', views.review_list, name='review_list'),
    path('api/', views.review_list_api, name='review_list_api'),
]
