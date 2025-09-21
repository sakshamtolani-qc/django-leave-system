# documents/urls.py
from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    # ID Cards
    path('id-card/generate/<int:employee_id>/', views.generate_id_card, name='generate_id_card'),
    path('id-card/<int:employee_id>/', views.id_card_view, name='id_card_view'),
    
    # Offer Letters
    path('offer-letter/create/<int:employee_id>/', views.create_offer_letter, name='create_offer_letter'),
    path('offer-letter/<int:pk>/', views.offer_letter_detail, name='offer_letter_detail'),
    path('offer-letter/<int:pk>/download/', views.download_offer_letter, name='download_offer_letter'),
    path('offer-letter/<int:pk>/send/', views.send_offer_letter, name='send_offer_letter'),
    path('offer-letter/<int:pk>/edit/', views.edit_offer_letter, name='edit_offer_letter'),
    
    # Document listing
    path('', views.document_dashboard, name='dashboard'),
]