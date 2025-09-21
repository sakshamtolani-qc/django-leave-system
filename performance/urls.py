# performance/urls.py
from django.urls import path
from . import views

app_name = 'performance'

urlpatterns = [
    path('', views.performance_dashboard, name='dashboard'),
    path('create/<int:employee_id>/', views.create_performance_review, name='create_review'),
    path('review/<int:pk>/', views.review_detail, name='review_detail'),
    path('review/<int:pk>/edit/', views.edit_review, name='edit_review'),
    path('review/<int:pk>/comment/', views.add_employee_comment, name='add_employee_comment'),
    path('my-reviews/', views.my_reviews, name='my_reviews'),
    path('bulk-create/', views.bulk_review_creation, name='bulk_review'),
]