from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth
from django.utils import timezone
from datetime import date, datetime
from .models import Client, Chambre, Reservation, Sejour, Paiement, ServiceSupplementaire, ReservationService
from .forms import ClientForm, ChambreForm, ReservationForm, SejourForm, PaiementForm

def login_view(request):
    """Vue de connexion pour les utilisateurs"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.username} !')
            
            # Rediriger vers la page demandée ou le dashboard
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'gestion/login.html')

def logout_view(request):
    """Vue de déconnexion"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('login')

@login_required
def dashboard(request):
    # Statistiques chambres
    total_chambres = Chambre.objects.count()
    chambres_disponibles = Chambre.objects.filter(statut='DISPONIBLE').count()
    chambres_occupees = Chambre.objects.filter(statut='OCCUPEE').count()
    
    # Arrivées et départs aujourd'hui
    today = date.today()
    reservations_aujourdhui = Reservation.objects.filter(
        date_debut_sejour=today,
        statut='CONFIRMEE'
    ).count()
    
    departs_aujourdhui = Reservation.objects.filter(
        date_fin_sejour=today,
        statut='CONFIRMEE'
    ).count()
    
    # Séjours actifs (ceux qui n'ont pas encore fait de check-out)
    sejours_actifs = Sejour.objects.filter(date_checkout__isnull=True).count()
    
    # Revenus du mois
    revenus_mois = Paiement.objects.filter(
        date_paiement__year=today.year,
        date_paiement__month=today.month,
        statut='VALIDE'
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    # Réservations récentes
    reservations_recentes = Reservation.objects.select_related(
        'client', 'chambre'
    ).order_by('-date_reservation')[:5]
    
    # Statistiques générales
    total_clients = Client.objects.count()
    total_reservations = Reservation.objects.count()
    reservations_confirmees = Reservation.objects.filter(statut='CONFIRMEE').count()
    
    # Vérifier si l'utilisateur est admin ou réceptionniste
    is_admin = request.user.is_superuser or (
        hasattr(request.user, 'utilisateur') and 
        request.user.utilisateur.role == 'ADMIN'
    )
    
    # Données spécifiques aux admins
    if is_admin:
        # Revenus total (seulement pour admin)
        revenus_total = Paiement.objects.filter(statut='VALIDE').aggregate(
            total=Sum('montant')
        )['total'] or 0
        
        # Chambres par type
        chambres_par_type = Chambre.objects.values('type_chambre').annotate(
            count=Count('id')
        )
        
        # Réservations par mois (derniers 6 mois)
        reservations_par_mois = Reservation.objects.annotate(
            mois=TruncMonth('date_reservation')
        ).values('mois').annotate(count=Count('id')).order_by('-mois')[:6]
    else:
        # Pour réceptionnistes : pas d'accès aux données sensibles
        revenus_total = None
        chambres_par_type = None
        reservations_par_mois = None
    
    # Vérifier les permissions de l'utilisateur
    user_permissions = {
        'can_add_client': request.user.has_perm('gestion.add_client'),
        'can_add_chambre': request.user.has_perm('gestion.add_chambre'),
        'can_add_reservation': request.user.has_perm('gestion.add_reservation'),
        'can_add_sejour': request.user.has_perm('gestion.add_sejour'),
        'can_add_paiement': request.user.has_perm('gestion.add_paiement'),
    }
    
    context = {
        # Données communes
        'total_chambres': total_chambres,
        'chambres_disponibles': chambres_disponibles,
        'chambres_occupees': chambres_occupees,
        'reservations_aujourdhui': reservations_aujourdhui,
        'departs_aujourdhui': departs_aujourdhui,
        'sejours_actifs': sejours_actifs,
        'revenus_mois': revenus_mois,
        'reservations_recentes': reservations_recentes,
        'user_permissions': user_permissions,
        'total_clients': total_clients,
        'total_reservations': total_reservations,
        'reservations_confirmees': reservations_confirmees,
        
        # Données spécifiques
        'is_admin': is_admin,
        'revenus_total': revenus_total,
        'chambres_par_type': chambres_par_type,
        'reservations_par_mois': reservations_par_mois,
    }
    
    return render(request, 'gestion/dashboard.html', context)

# ============ GESTION DES CLIENTS ============

@login_required
def client_list(request):
    search = request.GET.get('search', '')
    if search:
        clients = Client.objects.filter(
            Q(nom__icontains=search) |
            Q(prenom__icontains=search) |
            Q(email__icontains=search) |
            Q(telephone__icontains=search)
        ).order_by('-date_inscription')
    else:
        clients = Client.objects.all().order_by('-date_inscription')
    
    context = {
        'clients': clients,
        'search': search,
    }
    return render(request, 'gestion/client_list.html', context)

@login_required
def client_create(request):
    if request.method == 'POST':
        # Récupérer les données du formulaire
        nom = request.POST.get('nom')
        prenom = request.POST.get('prenom')
        email = request.POST.get('email')
        telephone = request.POST.get('telephone')
        date_naissance = request.POST.get('date_naissance') or None
        piece_identite = request.POST.get('piece_identite')
        numero_piece = request.POST.get('numero_piece')
        adresse = request.POST.get('adresse')
        ville = request.POST.get('ville')
        pays = request.POST.get('pays')
        
        # Vérifier si l'email existe déjà
        if Client.objects.filter(email=email).exists():
            messages.error(request, f'Un client avec l\'email {email} existe déjà !')
            return render(request, 'gestion/client_form.html')
        
        # Vérifier si le téléphone existe déjà
        if Client.objects.filter(telephone=telephone).exists():
            messages.error(request, f'Un client avec le téléphone {telephone} existe déjà !')
            return render(request, 'gestion/client_form.html')
        
        # Vérifier si le numéro de pièce existe déjà
        if Client.objects.filter(numero_piece=numero_piece).exists():
            messages.error(request, f'Un client avec le numéro de pièce {numero_piece} existe déjà !')
            return render(request, 'gestion/client_form.html')
        
        # Créer le client
        try:
            client = Client.objects.create(
                nom=nom,
                prenom=prenom,
                email=email,
                telephone=telephone,
                date_naissance=date_naissance,
                piece_identite=piece_identite,
                numero_piece=numero_piece,
                adresse=adresse,
                ville=ville,
                pays=pays
            )
            
            messages.success(request, f'Client {client.nom_complet} créé avec succès !')
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du client : {str(e)}')
            return render(request, 'gestion/client_form.html')
    
    return render(request, 'gestion/client_form.html')

@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f'Client {client.nom} {client.prenom} modifié avec succès.')
            return redirect('client_list')
    else:
        form = ClientForm(instance=client)
    
    context = {'form': form, 'client': client}
    return render(request, 'gestion/client_form.html', context)

@login_required
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    if request.method == 'POST':
        nom_complet = f'{client.nom} {client.prenom}'
        client.delete()
        messages.success(request, f'Client {nom_complet} supprimé avec succès.')
        return redirect('client_list')
    
    context = {'client': client}
    return render(request, 'gestion/client_confirm_delete.html', context)

@login_required
def client_detail(request, pk):
    client = get_object_or_404(Client, pk=pk)
    
    # Réservations du client
    reservations = Reservation.objects.filter(client=client).select_related('chambre').order_by('-date_reservation')
    
    # Statistiques
    total_reservations = reservations.count()
    total_sejours = Sejour.objects.filter(reservation__client=client).count()
    total_depense = Paiement.objects.filter(
        sejour__reservation__client=client,
        statut='VALIDE'
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    context = {
        'client': client,
        'reservations': reservations,
        'total_reservations': total_reservations,
        'total_sejours': total_sejours,
        'total_depense': total_depense,
    }
    return render(request, 'gestion/client_detail.html', context)

# ============ GESTION DES CHAMBRES ============

@login_required
def chambre_list(request):
    type_filtre = request.GET.get('type', '')
    statut_filtre = request.GET.get('statut', '')
    
    chambres = Chambre.objects.all()
    
    if type_filtre:
        chambres = chambres.filter(type_chambre=type_filtre)
    
    if statut_filtre:
        chambres = chambres.filter(statut=statut_filtre)
    
    # Statistiques
    total_chambres = Chambre.objects.count()
    chambres_disponibles = Chambre.objects.filter(statut='DISPONIBLE').count()
    
    context = {
        'chambres': chambres,
        'total_chambres': total_chambres,
        'chambres_disponibles': chambres_disponibles,
        'type_filtre': type_filtre,
        'statut_filtre': statut_filtre,
    }
    return render(request, 'gestion/chambre_list.html', context)

@login_required
def chambre_create(request):
    if request.method == 'POST':
        form = ChambreForm(request.POST)
        if form.is_valid():
            chambre = form.save()
            messages.success(request, f'Chambre {chambre.numero_chambre} créée avec succès.')
            return redirect('chambre_list')
    else:
        form = ChambreForm()
    
    context = {'form': form}
    return render(request, 'gestion/chambre_form.html', context)

@login_required
def chambre_update(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk)
    
    if request.method == 'POST':
        form = ChambreForm(request.POST, instance=chambre)
        if form.is_valid():
            form.save()
            messages.success(request, f'Chambre {chambre.numero_chambre} modifiée avec succès.')
            return redirect('chambre_list')
    else:
        form = ChambreForm(instance=chambre)
    
    context = {'form': form, 'chambre': chambre}
    return render(request, 'gestion/chambre_form.html', context)

@login_required
def chambre_delete(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk)
    
    if request.method == 'POST':
        numero = chambre.numero_chambre
        chambre.delete()
        messages.success(request, f'Chambre {numero} supprimée avec succès.')
        return redirect('chambre_list')
    
    context = {'chambre': chambre}
    return render(request, 'gestion/chambre_confirm_delete.html', context)

@login_required
def chambre_detail(request, pk):
    chambre = get_object_or_404(Chambre, pk=pk)
    
    # Réservations de cette chambre
    reservations_recentes = Reservation.objects.filter(
        chambre=chambre
    ).select_related('client').order_by('-date_reservation')[:10]
    
    # Statistiques
    reservations_count = Reservation.objects.filter(chambre=chambre).count()
    sejours_count = Sejour.objects.filter(reservation__chambre=chambre).count()
    revenus_total = Paiement.objects.filter(
        sejour__reservation__chambre=chambre,
        statut='VALIDE'
    ).aggregate(total=Sum('montant'))['total'] or 0
    
    context = {
        'chambre': chambre,
        'reservations_recentes': reservations_recentes,
        'reservations_count': reservations_count,
        'sejours_count': sejours_count,
        'revenus_total': revenus_total,
    }
    return render(request, 'gestion/chambre_detail.html', context)

# ============ GESTION DES RÉSERVATIONS ============

@login_required
def reservation_list(request):
    search = request.GET.get('search', '')
    statut_filtre = request.GET.get('statut', '')
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    reservations = Reservation.objects.select_related('client', 'chambre').all()
    
    if search:
        reservations = reservations.filter(
            Q(client__nom__icontains=search) |
            Q(client__prenom__icontains=search) |
            Q(chambre__numero_chambre__icontains=search)
        )
    
    if statut_filtre:
        reservations = reservations.filter(statut=statut_filtre)
    
    if date_debut:
        reservations = reservations.filter(date_debut_sejour__gte=date_debut)
    
    if date_fin:
        reservations = reservations.filter(date_fin_sejour__lte=date_fin)
    
    reservations = reservations.order_by('-date_reservation')
    
    context = {
        'reservations': reservations,
        'search': search,
        'statut_filtre': statut_filtre,
        'date_debut': date_debut,
        'date_fin': date_fin,
    }
    return render(request, 'gestion/reservation_list.html', context)

@login_required
def reservation_create(request):
    # Récupérer tous les clients
    clients = Client.objects.all().order_by('nom', 'prenom')
    
    # Récupérer seulement les chambres disponibles
    chambres = Chambre.objects.filter(statut='DISPONIBLE').order_by('numero_chambre')
    
    if request.method == 'POST':
        try:
            client_id = request.POST.get('client')
            chambre_id = request.POST.get('chambre')
            date_debut_sejour = request.POST.get('date_debut_sejour')
            date_fin_sejour = request.POST.get('date_fin_sejour')
            nombre_personnes = request.POST.get('nombre_personnes', 1)
            statut = request.POST.get('statut')
            commentaire = request.POST.get('commentaire', '')
            
            # Validation des données
            if not client_id or not chambre_id or not date_debut_sejour or not date_fin_sejour:
                messages.error(request, 'Veuillez remplir tous les champs obligatoires.')
                context = {'clients': clients, 'chambres': chambres}
                return render(request, 'gestion/reservation_form.html', context)
            
            # Calculer le nombre de nuits et le prix
            debut = datetime.strptime(date_debut_sejour, '%Y-%m-%d').date()
            fin = datetime.strptime(date_fin_sejour, '%Y-%m-%d').date()
            nombre_nuits = (fin - debut).days
            
            # Vérifier que la date de fin est après la date de début
            if nombre_nuits <= 0:
                messages.error(request, 'La date de départ doit être postérieure à la date d\'arrivée.')
                context = {'clients': clients, 'chambres': chambres}
                return render(request, 'gestion/reservation_form.html', context)
            
            # Récupérer la chambre pour obtenir le prix
            chambre = Chambre.objects.get(id=chambre_id)
            prix_total = chambre.prix_nuit * nombre_nuits
            
            # Convertir nombre_personnes en entier
            try:
                nombre_adultes = int(nombre_personnes)
                if nombre_adultes < 1:
                    nombre_adultes = 1
            except (ValueError, TypeError):
                nombre_adultes = 1
            
            # Créer la réservation
            reservation = Reservation.objects.create(
                client_id=client_id,
                chambre_id=chambre_id,
                utilisateur=request.user,
                date_debut_sejour=date_debut_sejour,
                date_fin_sejour=date_fin_sejour,
                nombre_nuits=nombre_nuits,
                nombre_adultes=nombre_adultes,
                nombre_enfants=0,
                nombre_personnes=nombre_adultes,
                prix_total=prix_total,
                statut=statut,
                commentaire=commentaire
            )
            
            messages.success(request, f'Réservation créée avec succès pour {reservation.client.nom_complet} !')
            return redirect('dashboard')
            
        except Chambre.DoesNotExist:
            messages.error(request, 'La chambre sélectionnée n\'existe pas.')
        except Client.DoesNotExist:
            messages.error(request, 'Le client sélectionné n\'existe pas.')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la réservation : {str(e)}')
    
    context = {
        'clients': clients,
        'chambres': chambres
    }
    return render(request, 'gestion/reservation_form.html', context)

@login_required
def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'POST':
        form = ReservationForm(request.POST, instance=reservation)
        if form.is_valid():
            form.save()
            messages.success(request, 'Réservation modifiée avec succès.')
            return redirect('reservation_list')
    else:
        form = ReservationForm(instance=reservation)
    
    context = {'form': form, 'reservation': reservation}
    return render(request, 'gestion/reservation_form.html', context)

@login_required
def reservation_delete(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    
    if request.method == 'POST':
        reservation.delete()
        messages.success(request, 'Réservation supprimée avec succès.')
        return redirect('reservation_list')
    
    context = {'reservation': reservation}
    return render(request, 'gestion/reservation_confirm_delete.html', context)

@login_required
def reservation_cancel(request, pk):
    """Annuler une réservation (et son séjour si existant)"""
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Vérifier que la réservation peut être annulée
    if reservation.statut == 'ANNULEE':
        messages.warning(request, 'Cette réservation est déjà annulée.')
        return redirect('reservation_list')
    
    if reservation.statut == 'TERMINEE':
        messages.error(request, 'Impossible d\'annuler une réservation terminée.')
        return redirect('reservation_list')
    
    # Afficher le formulaire de confirmation
    if request.method == 'GET':
        return render(request, 'gestion/reservation_cancel_confirm.html', {
            'reservation': reservation
        })
    
    # Traiter l'annulation
    if request.method == 'POST':
        motif_annulation = request.POST.get('motif_annulation', '')
        commentaire_annulation = request.POST.get('commentaire_annulation', '')
        
        # Vérifier que le motif est fourni
        if not motif_annulation:
            messages.error(request, 'Le motif d\'annulation est obligatoire.')
            return render(request, 'gestion/reservation_cancel_confirm.html', {
                'reservation': reservation
            })
        
        try:
            # Si un séjour existe, le supprimer d'abord
            if hasattr(reservation, 'sejour'):
                sejour = reservation.sejour
                
                # Vérifier s'il y a des paiements associés au séjour
                paiements = Paiement.objects.filter(sejour=sejour)
                if paiements.exists():
                    # Marquer les paiements comme remboursés
                    paiements.update(statut='REMBOURSE')
                    messages.info(request, f'{paiements.count()} paiement(s) marqué(s) comme remboursé(s).')
                
                # Supprimer le séjour
                sejour.delete()
                messages.info(request, 'Le séjour associé a été supprimé.')
            
            # Construire le commentaire complet
            commentaire_complet = f"[ANNULATION - {timezone.now().strftime('%d/%m/%Y %H:%M')}]\n"
            commentaire_complet += f"Motif: {motif_annulation}\n"
            commentaire_complet += f"Par: {request.user.username}\n"
            if commentaire_annulation:
                commentaire_complet += f"Détails: {commentaire_annulation}\n"
            
            # Ajouter au commentaire existant
            if reservation.commentaire:
                reservation.commentaire += f"\n\n{commentaire_complet}"
            else:
                reservation.commentaire = commentaire_complet
            
            # Annuler la réservation
            reservation.statut = 'ANNULEE'
            reservation.save()
            
            # Libérer la chambre
            chambre = reservation.chambre
            if chambre.statut == 'OCCUPEE':
                chambre.statut = 'DISPONIBLE'
                chambre.save()
                messages.info(request, f'La chambre {chambre.numero_chambre} a été libérée.')
            
            messages.success(request, f'✅ Réservation #{reservation.id} annulée avec succès. Motif: {motif_annulation}')
            
        except Exception as e:
            messages.error(request, f'❌ Erreur lors de l\'annulation : {str(e)}')
        
        return redirect('reservation_list')

@login_required
def reservation_detail(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    
    # Séjour associé
    try:
        sejour = Sejour.objects.get(reservation=reservation)
    except Sejour.DoesNotExist:
        sejour = None
    
    # Paiements
    paiements = Paiement.objects.filter(sejour=sejour) if sejour else []
    
    context = {
        'reservation': reservation,
        'sejour': sejour,
        'paiements': paiements,
    }
    return render(request, 'gestion/reservation_detail.html', context)

# ============ GESTION DES SÉJOURS ============

@login_required
def sejour_list(request):
    sejours = Sejour.objects.select_related(
        'reservation', 'reservation__client', 'reservation__chambre'
    ).order_by('-date_checkin')
    
    context = {
        'sejours': sejours,
    }
    return render(request, 'gestion/sejour_list.html', context)

@login_required
def sejour_create(request):
    if request.method == 'POST':
        form = SejourForm(request.POST)
        if form.is_valid():
            sejour = form.save()
            messages.success(request, 'Séjour créé avec succès.')
            return redirect('sejour_list')
    else:
        form = SejourForm()
    
    context = {'form': form}
    return render(request, 'gestion/sejour_form.html', context)

@login_required
def sejour_update(request, pk):
    sejour = get_object_or_404(Sejour, pk=pk)
    
    if request.method == 'POST':
        form = SejourForm(request.POST, instance=sejour)
        if form.is_valid():
            form.save()
            messages.success(request, 'Séjour modifié avec succès.')
            return redirect('sejour_list')
    else:
        form = SejourForm(instance=sejour)
    
    context = {'form': form, 'sejour': sejour}
    return render(request, 'gestion/sejour_form.html', context)

@login_required
def sejour_delete(request, pk):
    sejour = get_object_or_404(Sejour, pk=pk)
    
    if request.method == 'POST':
        sejour.delete()
        messages.success(request, 'Séjour supprimé avec succès.')
        return redirect('sejour_list')
    
    context = {'sejour': sejour}
    return render(request, 'gestion/sejour_confirm_delete.html', context)

@login_required
def sejour_detail(request, pk):
    sejour = get_object_or_404(Sejour, pk=pk)
    
    # Paiements du séjour
    paiements = Paiement.objects.filter(sejour=sejour).order_by('-date_paiement')
    
    # Services supplémentaires
    services = ReservationService.objects.filter(reservation=sejour.reservation).select_related('service')
    
    context = {
        'sejour': sejour,
        'paiements': paiements,
        'services': services,
    }
    return render(request, 'gestion/sejour_detail.html', context)

# ============ CHECK-IN ET CHECK-OUT ============

@login_required
def sejour_checkin(request, reservation_id):
    """Effectuer le check-in d'une réservation"""
    reservation = get_object_or_404(Reservation, pk=reservation_id)
    
    # Vérifier que la réservation est confirmée
    if reservation.statut != 'CONFIRMEE':
        messages.error(request, 'Seules les réservations confirmées peuvent faire un check-in.')
        return redirect('reservation_list')
    
    # Vérifier qu'il n'y a pas déjà un séjour
    if hasattr(reservation, 'sejour'):
        messages.warning(request, 'Cette réservation a déjà fait son check-in.')
        return redirect('sejour_detail', pk=reservation.sejour.id)
    
    if request.method == 'POST':
        date_arrivee_effective = request.POST.get('date_arrivee_effective')
        nombre_personnes = request.POST.get('nombre_personnes', reservation.nombre_adultes + reservation.nombre_enfants)
        commentaire = request.POST.get('commentaire', '')
        
        try:
            # Créer le séjour
            sejour = Sejour.objects.create(
                reservation=reservation,
                date_arrivee_effective=date_arrivee_effective,
                nombre_personnes=int(nombre_personnes),
                commentaire=commentaire
            )
            
            messages.success(request, f'Check-in effectué avec succès pour {reservation.client.nom_complet} !')
            return redirect('sejour_detail', pk=sejour.id)
            
        except Exception as e:
            messages.error(request, f'Erreur lors du check-in : {str(e)}')
    
    # Préparer la date/heure actuelle pour le formulaire
    now = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    context = {
        'reservation': reservation,
        'now': now,
    }
    return render(request, 'gestion/sejour_checkin_form.html', context)


@login_required
def sejour_checkout(request, sejour_id):
    """Effectuer le check-out d'un séjour"""
    sejour = get_object_or_404(Sejour, pk=sejour_id)
    
    # Vérifier que le séjour n'est pas déjà terminé
    if sejour.date_checkout:
        messages.warning(request, 'Ce séjour a déjà fait son check-out.')
        return redirect('sejour_detail', pk=sejour.id)
    
    if request.method == 'POST':
        date_depart_effective = request.POST.get('date_depart_effective')
        commentaire = request.POST.get('commentaire', '')
        
        try:
            # Vérifier que tous les paiements sont effectués
            solde_restant = sejour.solde_restant
            
            if solde_restant > 0:
                messages.error(request, f'Impossible de faire le check-out. Solde restant : {solde_restant} GNF')
                return redirect('sejour_detail', pk=sejour.id)
            
            # Effectuer le check-out
            sejour.date_depart_effective = date_depart_effective
            sejour.date_checkout = timezone.now()
            if commentaire:
                sejour.commentaire = f"{sejour.commentaire}\n{commentaire}" if sejour.commentaire else commentaire
            sejour.save()
            
            messages.success(request, f'Check-out effectué avec succès pour {sejour.reservation.client.nom_complet} !')
            return redirect('sejour_list')
            
        except Exception as e:
            messages.error(request, f'Erreur lors du check-out : {str(e)}')
    
    # Préparer la date/heure actuelle pour le formulaire
    now = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    # Calculer les informations de paiement
    total_a_payer = sejour.reservation.montant_total_avec_services
    total_paye = sejour.montant_total_paye
    solde_restant = sejour.solde_restant
    
    context = {
        'sejour': sejour,
        'now': now,
        'total_a_payer': total_a_payer,
        'total_paye': total_paye,
        'solde_restant': solde_restant,
    }
    return render(request, 'gestion/sejour_checkout_form.html', context)

# ============ GESTION DES PAIEMENTS ============

@login_required
def paiement_list(request):
    mode_filtre = request.GET.get('mode', '')
    statut_filtre = request.GET.get('statut', '')
    
    paiements = Paiement.objects.select_related(
        'sejour', 'sejour__reservation__client'
    ).all()
    
    if mode_filtre:
        paiements = paiements.filter(mode_paiement=mode_filtre)
    
    if statut_filtre:
        paiements = paiements.filter(statut=statut_filtre)
    
    paiements = paiements.order_by('-date_paiement')
    
    # Total des paiements
    total_paiements = Paiement.objects.filter(statut='VALIDE').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    context = {
        'paiements': paiements,
        'total_paiements': total_paiements,
        'mode_filtre': mode_filtre,
        'statut_filtre': statut_filtre,
    }
    return render(request, 'gestion/paiement_list.html', context)

@login_required
def paiement_create(request):
    # Récupérer tous les séjours actifs (pas encore terminés)
    sejours = Sejour.objects.filter(date_checkout__isnull=True).select_related(
        'reservation__client', 'reservation__chambre'
    ).order_by('-date_checkin')
    
    if request.method == 'POST':
        sejour_id = request.POST.get('sejour')
        montant = request.POST.get('montant')
        mode_paiement = request.POST.get('mode_paiement')
        statut = request.POST.get('statut')
        reference_transaction = request.POST.get('reference_transaction')
        
        # Générer une référence si elle n'est pas fournie
        if not reference_transaction:
            reference_transaction = f"PAY-{datetime.now().strftime('%Y%m%d')}-{Paiement.objects.count() + 1:06d}"
        
        # Créer le paiement
        paiement = Paiement.objects.create(
            sejour_id=sejour_id,
            montant=montant,
            mode_paiement=mode_paiement,
            statut=statut,
            reference_transaction=reference_transaction
        )
        
        messages.success(request, f'Paiement de {paiement.montant} GNF enregistré avec succès !')
        return redirect('dashboard')
    
    context = {'sejours': sejours}
    return render(request, 'gestion/paiement_form.html', context)

@login_required
def paiement_update(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    
    if request.method == 'POST':
        form = PaiementForm(request.POST, instance=paiement)
        if form.is_valid():
            form.save()
            messages.success(request, 'Paiement modifié avec succès.')
            return redirect('paiement_list')
    else:
        form = PaiementForm(instance=paiement)
    
    context = {'form': form, 'paiement': paiement}
    return render(request, 'gestion/paiement_form.html', context)

@login_required
def paiement_delete(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    
    if request.method == 'POST':
        paiement.delete()
        messages.success(request, 'Paiement supprimé avec succès.')
        return redirect('paiement_list')
    
    context = {'paiement': paiement}
    return render(request, 'gestion/paiement_confirm_delete.html', context)

# ============ RAPPORTS ============

@login_required
def rapports(request):
    # Statistiques générales
    total_clients = Client.objects.count()
    total_reservations = Reservation.objects.count()
    reservations_confirmees = Reservation.objects.filter(statut='CONFIRMEE').count()
    
    # Revenus total
    revenus_total = Paiement.objects.filter(statut='VALIDE').aggregate(
        total=Sum('montant')
    )['total'] or 0
    
    # Chambres par type
    chambres_par_type = Chambre.objects.values('type_chambre').annotate(
        count=Count('id')
    )
    
    # Réservations par mois (derniers 6 mois)
    reservations_par_mois = Reservation.objects.annotate(
        mois=TruncMonth('date_reservation')
    ).values('mois').annotate(count=Count('id')).order_by('-mois')[:6]
    
    # Taux d'occupation
    total_chambres = Chambre.objects.count()
    chambres_occupees = Chambre.objects.filter(statut='OCCUPEE').count()
    taux_occupation = (chambres_occupees / total_chambres * 100) if total_chambres > 0 else 0
    
    # Revenu moyen par réservation
    revenu_moyen = revenus_total / total_reservations if total_reservations > 0 else 0
    
    context = {
        'total_clients': total_clients,
        'total_reservations': total_reservations,
        'reservations_confirmees': reservations_confirmees,
        'revenus_total': revenus_total,
        'chambres_par_type': chambres_par_type,
        'reservations_par_mois': reservations_par_mois,
        'taux_occupation': round(taux_occupation, 2),
        'revenu_moyen': revenu_moyen,
    }
    return render(request, 'gestion/rapports.html', context)