from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Client, Chambre, Reservation, Sejour, Paiement, ServiceSupplementaire

# Formulaire de création de client
class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            'nom', 'prenom', 'email', 'telephone', 'adresse', 
            'ville', 'pays', 'piece_identite', 'numero_piece', 'date_naissance'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse complète'}),
            'ville': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ville'}),
            'pays': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pays'}),
            'piece_identite': forms.Select(attrs={'class': 'form-control'}),
            'numero_piece': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de pièce'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# Formulaire de création de chambre
class ChambreForm(forms.ModelForm):
    class Meta:
        model = Chambre
        fields = [
            'numero_chambre', 'type_chambre', 'prix_nuit', 
            'nombre_lits', 'superficie', 'etage', 'description', 'statut'
        ]
        widgets = {
            'numero_chambre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 101'}),
            'type_chambre': forms.Select(attrs={'class': 'form-control'}),
            'prix_nuit': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix par nuit'}),
            'nombre_lits': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de lits'}),
            'superficie': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Superficie en m²'}),
            'etage': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Numéro d\'étage'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
        }


# Formulaire de recherche de disponibilité
class DisponibiliteChambreForm(forms.Form):
    date_debut = forms.DateField(
        label='Date d\'arrivée',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_fin = forms.DateField(
        label='Date de départ',
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    type_chambre = forms.ChoiceField(
        label='Type de chambre',
        choices=[('', 'Tous les types')] + list(Chambre.TYPE_CHAMBRE_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        
        if date_debut and date_fin:
            if date_fin <= date_debut:
                raise forms.ValidationError("La date de départ doit être postérieure à la date d'arrivée.")
        
        return cleaned_data


# Formulaire de création de réservation
class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = [
            'client', 'chambre', 'date_debut_sejour', 'date_fin_sejour',
            'nombre_adultes', 'nombre_enfants', 'commentaire'
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-control'}),
            'chambre': forms.Select(attrs={'class': 'form-control'}),
            'date_debut_sejour': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin_sejour': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'nombre_adultes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre d\'adultes'}),
            'nombre_enfants': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre d\'enfants'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Commentaires'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrer uniquement les chambres disponibles
        self.fields['chambre'].queryset = Chambre.objects.filter(statut='DISPONIBLE')


# Formulaire de création de séjour (Check-in)
class SejourForm(forms.ModelForm):
    class Meta:
        model = Sejour
        fields = ['reservation', 'date_arrivee_effective', 'nombre_personnes', 'commentaire']
        widgets = {
            'reservation': forms.Select(attrs={'class': 'form-control'}),
            'date_arrivee_effective': forms.DateTimeInput(attrs={
                'class': 'form-control', 
                'type': 'datetime-local'
            }),
            'nombre_personnes': forms.NumberInput(attrs={'class': 'form-control'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Afficher uniquement les réservations confirmées sans séjour
        self.fields['reservation'].queryset = Reservation.objects.filter(
            statut='CONFIRMEE'
        ).exclude(sejour__isnull=False)


# Formulaire de check-out
class CheckoutForm(forms.Form):
    date_depart_effective = forms.DateTimeField(
        label='Date et heure de départ',
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control', 
            'type': 'datetime-local'
        })
    )
    commentaire = forms.CharField(
        label='Commentaire',
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )


# Formulaire de paiement
class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['sejour', 'montant', 'mode_paiement']
        widgets = {
            'sejour': forms.Select(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Montant'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Afficher uniquement les séjours non terminés
        self.fields['sejour'].queryset = Sejour.objects.filter(date_checkout__isnull=True)


# Formulaire de connexion personnalisé
class LoginForm(forms.Form):
    username = forms.CharField(
        label='Nom d\'utilisateur',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'})
    )
    password = forms.CharField(
        label='Mot de passe',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Mot de passe'})
    )


# Formulaire de service supplémentaire
class ServiceSupplementaireForm(forms.ModelForm):
    class Meta:
        model = ServiceSupplementaire
        fields = ['nom_service', 'description', 'prix', 'statut_actif']
        widgets = {
            'nom_service': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du service'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix'}),
            'statut_actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


# Formulaire de recherche de client
class ClientSearchForm(forms.Form):
    search = forms.CharField(
        label='Rechercher un client',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Nom, prénom, email ou téléphone'
        })
    )


# Formulaire de recherche de réservation
class ReservationSearchForm(forms.Form):
    search = forms.CharField(
        label='Rechercher',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Client, chambre ou numéro de réservation'
        })
    )
    statut = forms.ChoiceField(
        label='Statut',
        choices=[('', 'Tous')] + list(Reservation.STATUT_CHOICES),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    date_debut = forms.DateField(
        label='Date de début',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    date_fin = forms.DateField(
        label='Date de fin',
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}) )