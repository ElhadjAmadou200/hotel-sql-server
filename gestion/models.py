from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.utils import timezone

# Modèle Utilisateur étendu
class Utilisateur(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Administrateur'),
        ('RECEPTIONNISTE', 'Réceptionniste'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='utilisateur')
    telephone = models.CharField(max_length=20)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    statut_actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Utilisateur"
        verbose_name_plural = "Utilisateurs"
    
    def __str__(self):
        return f"{self.user.first_name} {self.user.last_name} - {self.get_role_display()}"


# Modèle Client
class Client(models.Model):
    PIECE_IDENTITE_CHOICES = [
        ('CNI', 'Carte Nationale d\'Identité'),
        ('PASSEPORT', 'Passeport'),
        ('PERMIS', 'Permis de conduire'),
    ]
    
    nom = models.CharField(max_length=50)
    prenom = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=20)
    adresse = models.TextField()
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100, default='Guinée')
    piece_identite = models.CharField(max_length=20, choices=PIECE_IDENTITE_CHOICES)
    numero_piece = models.CharField(max_length=50, unique=True)
    date_naissance = models.DateField()
    date_inscription = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        ordering = ['-date_inscription']
    
    def __str__(self):
        return f"{self.nom} {self.prenom}"
    
    @property
    def nom_complet(self):
        return f"{self.prenom} {self.nom}"


# Modèle Chambre
class Chambre(models.Model):
    TYPE_CHAMBRE_CHOICES = [
        ('SIMPLE', 'Simple'),
        ('DOUBLE', 'Double'),
        ('SUITE', 'Suite'),
        ('DELUXE', 'Deluxe'),
    ]
    
    STATUT_CHOICES = [
        ('DISPONIBLE', 'Disponible'),
        ('OCCUPEE', 'Occupée'),
        ('MAINTENANCE', 'En maintenance'),
        ('HORS_SERVICE', 'Hors service'),
    ]
    
    numero_chambre = models.CharField(max_length=10, unique=True)
    type_chambre = models.CharField(max_length=20, choices=TYPE_CHAMBRE_CHOICES)
    prix_nuit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    nombre_lits = models.IntegerField(validators=[MinValueValidator(1)])
    superficie = models.DecimalField(max_digits=5, decimal_places=2, help_text="Superficie en m²")
    etage = models.IntegerField()
    description = models.TextField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='DISPONIBLE')
    
    class Meta:
        verbose_name = "Chambre"
        verbose_name_plural = "Chambres"
        ordering = ['numero_chambre']
    
    def __str__(self):
        return f"Chambre {self.numero_chambre} - {self.get_type_chambre_display()}"
    
    def est_disponible(self, date_debut, date_fin):
        """Vérifie si la chambre est disponible pour une période donnée"""
        reservations_conflictuelles = self.reservation_set.filter(
            statut__in=['EN_ATTENTE', 'CONFIRMEE'],
            date_debut_sejour__lt=date_fin,
            date_fin_sejour__gt=date_debut
        )
        return not reservations_conflictuelles.exists() and self.statut == 'DISPONIBLE'


# Modèle Service Supplémentaire
class ServiceSupplementaire(models.Model):
    nom_service = models.CharField(max_length=100)
    description = models.TextField()
    prix = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    statut_actif = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = "Service Supplémentaire"
        verbose_name_plural = "Services Supplémentaires"
    
    def __str__(self):
        return f"{self.nom_service} - {self.prix} GNF"


# Modèle Réservation
class Reservation(models.Model):
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('CONFIRMEE', 'Confirmée'),
        ('ANNULEE', 'Annulée'),
        ('TERMINEE', 'Terminée'),
    ]
    
    client = models.ForeignKey(Client, on_delete=models.PROTECT)
    chambre = models.ForeignKey(Chambre, on_delete=models.PROTECT)
    utilisateur = models.ForeignKey(User, on_delete=models.PROTECT, related_name='reservations_gerees')
    
    date_reservation = models.DateTimeField(auto_now_add=True)
    date_debut_sejour = models.DateField()
    date_fin_sejour = models.DateField()
    nombre_adultes = models.IntegerField(validators=[MinValueValidator(1)])
    nombre_enfants = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    nombre_personnes = models.IntegerField(default=1, validators=[MinValueValidator(1)])  # ✅ AJOUTÉ
    nombre_nuits = models.IntegerField(editable=False)
    prix_total = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    commentaire = models.TextField(blank=True, null=True)
    
    services_supplementaires = models.ManyToManyField(
        ServiceSupplementaire,
        through='ReservationService',
        related_name='reservations'
    )
    
    class Meta:
        verbose_name = "Réservation"
        verbose_name_plural = "Réservations"
        ordering = ['-date_reservation']
    
    def __str__(self):
        return f"Réservation #{self.id} - {self.client.nom_complet} - Chambre {self.chambre.numero_chambre}"
    
    def save(self, *args, **kwargs):
        # Calculer automatiquement le nombre de nuits
        if self.date_debut_sejour and self.date_fin_sejour:
            self.nombre_nuits = (self.date_fin_sejour - self.date_debut_sejour).days
        
        # Calculer le prix total si non défini
        if not self.prix_total and self.chambre:
            self.prix_total = self.chambre.prix_nuit * self.nombre_nuits
        
        super().save(*args, **kwargs)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Vérifier que la date de fin est après la date de début
        if self.date_debut_sejour and self.date_fin_sejour:
            if self.date_fin_sejour <= self.date_debut_sejour:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")
        
        # Vérifier la disponibilité de la chambre
        if self.chambre and self.date_debut_sejour and self.date_fin_sejour:
            if not self.chambre.est_disponible(self.date_debut_sejour, self.date_fin_sejour):
                raise ValidationError("La chambre n'est pas disponible pour cette période.")
    
    @property
    def montant_services(self):
        """Calcule le montant total des services supplémentaires"""
        return sum(rs.montant_total for rs in self.reservationservice_set.all())
    
    @property
    def montant_total_avec_services(self):
        """Calcule le montant total incluant les services"""
        return self.prix_total + self.montant_services


# Modèle Réservation-Service (Table d'association)
class ReservationService(models.Model):
    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE)
    service = models.ForeignKey(ServiceSupplementaire, on_delete=models.PROTECT)
    quantite = models.IntegerField(validators=[MinValueValidator(1)])
    prix_unitaire = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        verbose_name = "Service de Réservation"
        verbose_name_plural = "Services de Réservation"
        unique_together = ['reservation', 'service']
    
    def __str__(self):
        return f"{self.service.nom_service} x{self.quantite} - Réservation #{self.reservation.id}"
    
    @property
    def montant_total(self):
        return self.quantite * self.prix_unitaire
    
    def save(self, *args, **kwargs):
        # Utiliser le prix actuel du service si non défini
        if not self.prix_unitaire:
            self.prix_unitaire = self.service.prix
        super().save(*args, **kwargs)


# Modèle Séjour
class Sejour(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.PROTECT)
    
    date_arrivee_effective = models.DateTimeField()
    date_depart_effective = models.DateTimeField(blank=True, null=True)
    date_checkin = models.DateTimeField(auto_now_add=True)
    date_checkout = models.DateTimeField(blank=True, null=True)
    nombre_personnes = models.IntegerField()
    commentaire = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Séjour"
        verbose_name_plural = "Séjours"
        ordering = ['-date_checkin']
    
    def __str__(self):
        return f"Séjour #{self.id} - {self.reservation.client.nom_complet}"
    
    def save(self, *args, **kwargs):
        # Mettre à jour le statut de la réservation et de la chambre
        if not self.pk:  # Nouveau séjour
            self.reservation.statut = 'CONFIRMEE'
            self.reservation.chambre.statut = 'OCCUPEE'
            self.reservation.save()
            self.reservation.chambre.save()
        
        # Si checkout, libérer la chambre
        if self.date_checkout and not self.date_depart_effective:
            self.date_depart_effective = timezone.now()
            self.reservation.chambre.statut = 'DISPONIBLE'
            self.reservation.statut = 'TERMINEE'
            self.reservation.chambre.save()
            self.reservation.save()
        
        super().save(*args, **kwargs)
    
    @property
    def est_termine(self):
        return self.date_checkout is not None
    
    @property
    def montant_total_paye(self):
        """Calcule le montant total payé pour ce séjour"""
        return sum(p.montant for p in self.paiement_set.filter(statut='VALIDE'))
    
    @property
    def solde_restant(self):
        """Calcule le solde restant à payer"""
        return self.reservation.montant_total_avec_services - self.montant_total_paye


# Modèle Paiement
class Paiement(models.Model):
    MODE_PAIEMENT_CHOICES = [
        ('ESPECES', 'Espèces'),
        ('CARTE', 'Carte bancaire'),
        ('VIREMENT', 'Virement'),
        ('MOBILE_MONEY', 'Mobile Money'),
    ]
    
    STATUT_CHOICES = [
        ('EN_ATTENTE', 'En attente'),
        ('VALIDE', 'Validé'),
        ('REMBOURSE', 'Remboursé'),
    ]
    
    sejour = models.ForeignKey(Sejour, on_delete=models.PROTECT)
    
    date_paiement = models.DateTimeField(auto_now_add=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    mode_paiement = models.CharField(max_length=30, choices=MODE_PAIEMENT_CHOICES)
    reference_transaction = models.CharField(max_length=100, unique=True)
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='EN_ATTENTE')
    
    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_paiement']
    
    def __str__(self):
        return f"Paiement #{self.id} - {self.montant} GNF - {self.get_mode_paiement_display()}"
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Vérifier que le montant ne dépasse pas le solde
        if self.sejour:
            solde_restant = self.sejour.solde_restant
            if self.montant > solde_restant:
                raise ValidationError(f"Le montant ne peut pas dépasser le solde restant ({solde_restant} GNF).")
    
    def save(self, *args, **kwargs):
        # Générer une référence de transaction si non fournie
        if not self.reference_transaction:
            import uuid
            self.reference_transaction = f"PAY-{uuid.uuid4().hex[:10].upper()}"
        
        super().save(*args, **kwargs)