from django.urls import path
from . import views

urlpatterns = [
    # Authentification
    path('', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Clients
    path('clients/', views.client_list, name='client_list'),
    path('clients/create/', views.client_create, name='client_create'),
    path('clients/<int:pk>/', views.client_detail, name='client_detail'),
    path('clients/<int:pk>/update/', views.client_update, name='client_update'),
    path('clients/<int:pk>/delete/', views.client_delete, name='client_delete'),
    
    # Chambres
    path('chambres/', views.chambre_list, name='chambre_list'),
    path('chambres/create/', views.chambre_create, name='chambre_create'),
    path('chambres/<int:pk>/', views.chambre_detail, name='chambre_detail'),
    path('chambres/<int:pk>/update/', views.chambre_update, name='chambre_update'),
    path('chambres/<int:pk>/delete/', views.chambre_delete, name='chambre_delete'),
    
    # Réservations
    path('reservations/', views.reservation_list, name='reservation_list'),
    path('reservations/create/', views.reservation_create, name='reservation_create'),
    path('reservations/<int:pk>/', views.reservation_detail, name='reservation_detail'),
    path('reservations/<int:pk>/update/', views.reservation_update, name='reservation_update'),
    path('reservations/<int:pk>/delete/', views.reservation_delete, name='reservation_delete'),
    path('reservations/<int:pk>/cancel/', views.reservation_cancel, name='reservation_cancel'),
    
    # Séjours
    path('sejours/', views.sejour_list, name='sejour_list'),
    path('sejours/create/', views.sejour_create, name='sejour_create'),
    path('sejours/<int:pk>/', views.sejour_detail, name='sejour_detail'),
    path('sejours/<int:pk>/update/', views.sejour_update, name='sejour_update'),
    path('sejours/<int:pk>/delete/', views.sejour_delete, name='sejour_delete'),
    
    # Check-in et Check-out
    path('sejours/checkin/<int:reservation_id>/', views.sejour_checkin, name='sejour_checkin'),
    path('sejours/checkout/<int:sejour_id>/', views.sejour_checkout, name='sejour_checkout'),
    
    # Paiements
    path('paiements/', views.paiement_list, name='paiement_list'),
    path('paiements/create/', views.paiement_create, name='paiement_create'),
    path('paiements/<int:pk>/update/', views.paiement_update, name='paiement_update'),
    path('paiements/<int:pk>/delete/', views.paiement_delete, name='paiement_delete'),
    
    # Rapports
    path('rapports/', views.rapports, name='rapports'),
]