from django.contrib import admin
from .models import (
    Utilisateur, Client, Chambre, ServiceSupplementaire,
    Reservation, ReservationService, Sejour, Paiement
)

# Configuration de l'admin pour Utilisateur
@admin.register(Utilisateur)
class UtilisateurAdmin(admin.ModelAdmin):
    list_display = ['get_nom_complet', 'role', 'telephone', 'statut_actif', 'date_creation']
    list_filter = ['role', 'statut_actif', 'date_creation']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'telephone']
    
    def get_nom_complet(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}"
    get_nom_complet.short_description = 'Nom complet'


# Configuration de l'admin pour Client
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ['nom', 'prenom', 'email', 'telephone', 'ville', 'pays', 'date_inscription']
    list_filter = ['pays', 'ville', 'piece_identite', 'date_inscription']
    search_fields = ['nom', 'prenom', 'email', 'telephone', 'numero_piece']
    date_hierarchy = 'date_inscription'
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'date_naissance')
        }),
        ('Adresse', {
            'fields': ('adresse', 'ville', 'pays')
        }),
        ('Identification', {
            'fields': ('piece_identite', 'numero_piece')
        }),
    )


# Configuration de l'admin pour Chambre
@admin.register(Chambre)
class ChambreAdmin(admin.ModelAdmin):
    list_display = ['numero_chambre', 'type_chambre', 'prix_nuit', 'nombre_lits', 'etage', 'statut']
    list_filter = ['type_chambre', 'statut', 'etage']
    search_fields = ['numero_chambre', 'description']
    list_editable = ['statut']
    
    fieldsets = (
        ('Informations de base', {
            'fields': ('numero_chambre', 'type_chambre', 'statut')
        }),
        ('Caractéristiques', {
            'fields': ('prix_nuit', 'nombre_lits', 'superficie', 'etage')
        }),
        ('Description', {
            'fields': ('description',)
        }),
    )


# Configuration de l'admin pour Service Supplémentaire
@admin.register(ServiceSupplementaire)
class ServiceSupplementaireAdmin(admin.ModelAdmin):
    list_display = ['nom_service', 'prix', 'statut_actif']
    list_filter = ['statut_actif']
    search_fields = ['nom_service', 'description']
    list_editable = ['statut_actif']


# Inline pour les services dans la réservation
class ReservationServiceInline(admin.TabularInline):
    model = ReservationService
    extra = 1
    fields = ['service', 'quantite', 'prix_unitaire']
    readonly_fields = []


# Configuration de l'admin pour Réservation
@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_client_nom', 'get_chambre', 'date_debut_sejour', 
        'date_fin_sejour', 'nombre_nuits', 'prix_total', 'statut'
    ]
    list_filter = ['statut', 'date_debut_sejour', 'date_reservation']
    search_fields = [
        'client__nom', 'client__prenom', 'chambre__numero_chambre',
        'utilisateur__first_name', 'utilisateur__last_name'
    ]
    date_hierarchy = 'date_reservation'
    inlines = [ReservationServiceInline]
    
    fieldsets = (
        ('Client et Chambre', {
            'fields': ('client', 'chambre', 'utilisateur')
        }),
        ('Dates', {
            'fields': ('date_debut_sejour', 'date_fin_sejour')
        }),
        ('Occupants', {
            'fields': ('nombre_adultes', 'nombre_enfants')
        }),
        ('Tarification', {
            'fields': ('prix_total', 'statut')
        }),
        ('Commentaire', {
            'fields': ('commentaire',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['nombre_nuits']
    
    def get_client_nom(self, obj):
        return obj.client.nom_complet
    get_client_nom.short_description = 'Client'
    
    def get_chambre(self, obj):
        return f"Chambre {obj.chambre.numero_chambre}"
    get_chambre.short_description = 'Chambre'


# Configuration de l'admin pour Séjour
@admin.register(Sejour)
class SejourAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_client', 'get_chambre', 'date_checkin', 
        'date_checkout', 'est_termine'
    ]
    list_filter = ['date_checkin', 'date_checkout']
    search_fields = [
        'reservation__client__nom', 'reservation__client__prenom',
        'reservation__chambre__numero_chambre'
    ]
    date_hierarchy = 'date_checkin'
    
    fieldsets = (
        ('Réservation', {
            'fields': ('reservation',)
        }),
        ('Dates', {
            'fields': ('date_arrivee_effective', 'date_depart_effective', 'date_checkin', 'date_checkout')
        }),
        ('Détails', {
            'fields': ('nombre_personnes', 'commentaire')
        }),
    )
    
    readonly_fields = ['date_checkin']
    
    def get_client(self, obj):
        return obj.reservation.client.nom_complet
    get_client.short_description = 'Client'
    
    def get_chambre(self, obj):
        return f"Chambre {obj.reservation.chambre.numero_chambre}"
    get_chambre.short_description = 'Chambre'


# Configuration de l'admin pour Paiement
@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'get_client', 'montant', 'mode_paiement', 
        'date_paiement', 'statut', 'reference_transaction'
    ]
    list_filter = ['mode_paiement', 'statut', 'date_paiement']
    search_fields = [
        'sejour__reservation__client__nom', 'sejour__reservation__client__prenom',
        'reference_transaction'
    ]
    date_hierarchy = 'date_paiement'
    
    fieldsets = (
        ('Séjour', {
            'fields': ('sejour',)
        }),
        ('Paiement', {
            'fields': ('montant', 'mode_paiement', 'reference_transaction')
        }),
        ('Statut', {
            'fields': ('statut',)
        }),
    )
    
    readonly_fields = ['date_paiement', 'reference_transaction']
    
    def get_client(self, obj):
        return obj.sejour.reservation.client.nom_complet
    get_client.short_description = 'Client'


# Configuration de l'admin pour ReservationService
@admin.register(ReservationService)
class ReservationServiceAdmin(admin.ModelAdmin):
    list_display = ['reservation', 'service', 'quantite', 'prix_unitaire', 'montant_total']
    list_filter = ['service']
    search_fields = ['reservation__client__nom', 'service__nom_service']
