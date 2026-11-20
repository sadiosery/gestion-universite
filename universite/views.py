import csv
import itertools
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model, login as auth_login
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import FileResponse, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from . import models, services
from .decorators import (consultation_uniquement, est_etudiant, est_personnel,
                         labo_uniquement, personnel_uniquement,
                         superuser_uniquement)
from .pages_catalogue import synchroniser_pages
from .sauvegarde import (creer_sauvegarde, dossier_sauvegardes,
                         lister_sauvegardes, purge_sauvegardes,
                         restaurer_sauvegarde)
from .forms import (AffectationUEForm, AnneeAcademiqueForm, BibliographieForm,
                    BourseForm, CommandeCantineForm, CoursEnLigneForm, CreneauForm,
                    DepartementForm,
                    EnseignantForm, EtudiantForm, EpreuveExamenForm,
                    ExperienceLaboForm, ExamenForm, FaculteForm, FiliereForm,
                    InscriptionForm, MenuJourForm, NoteForm, PaiementForm,
                    PlatCantineForm, PretOuvrageForm, RapportExperienceForm,
                    RechargeCantineForm, SalleForm, SemestreForm,
                    TypeFraisForm, UeForm, UniversiteParametreForm)


# ---------------------------------------------------------------------------
# Helpers d'affichage
# ---------------------------------------------------------------------------

def c(texte, url=None, badge=None):
    """Cellule de tableau : texte simple, lien ou badge coloré."""
    if url and not badge:
        return {'texte': texte, 'url': url}
    if badge and not url:
        return {'texte': texte, 'badge': badge}
    if url and badge:
        return {'texte': texte, 'url': url, 'badge': badge}
    return texte


_BADGES = {
    'actif': 'success', 'active': 'success', 'Present': 'success',
    'valide': 'success', 'validée': 'success', 'payee': 'success', 'payé': 'success',
    'en_cours': 'primary', 'programme': 'primary', 'en_attente': 'warning',
    'inactif': 'secondary', 'suspendu': 'warning', 'Absent': 'danger',
    'echoue': 'danger', 'non_payee': 'danger', 'retard': 'warning', 'Retard': 'warning',
    'en_conge': 'info', 'cloturee': 'secondary', 'clôturée': 'secondary',
    'diplome': 'info', 'exclu': 'dark', 'radie': 'dark', 'abandon': 'dark',
    'compense': 'info', 'credit': 'success',
    'publié': 'success', 'brouillon': 'warning',
}


def _badge(texte):
    return {'texte': texte, 'badge': _BADGES.get(texte.lower(), 'secondary')}


def _contexte_liste(titre, icone, colonnes, lignes, bouton=None, bouton_url='#'):
    return {
        'titre': titre, 'icone': icone, 'colonnes': colonnes,
        'lignes': lignes, 'bouton': bouton, 'bouton_url': bouton_url,
    }


def _maj(objet, prefixe, pk):
    return reverse(f'universite_{prefixe}_update', args=[pk])


def _pages_groupes(pages):
    """Regroupe les pages par section (ordre du catalogue)."""
    groupes = []
    for section, groupe in itertools.groupby(pages, key=lambda p: p.section):
        groupes.append((section, list(groupe)))
    return groupes


# ---------------------------------------------------------------------------
# Tableau de bord
# ---------------------------------------------------------------------------

@consultation_uniquement
def dashboard(request):
    if est_etudiant(request.user) and not est_personnel(request.user):
        etudiant = request.user.etudiant
        cgpa, credits, nb_valid = services.cgpa_etudiant(etudiant)
        annee = models.AnneeAcademique.objects.filter(active=True).first()
        menus = models.MenuJour.objects.filter(date=timezone.now().date()).select_related('plat')
        compte = models.CantineCompte.objects.filter(etudiant=etudiant).first()
        recentes_notes = (models.Note.objects.filter(etudiant=etudiant)
                          .select_related('ue').order_by('-date')[:8])
        nb_ues = 0
        if etudiant.filiere:
            nb_ues = models.UniteEnseignement.objects.filter(filiere=etudiant.filiere).count()
        return render(request, 'universite/dashboard_etudiant.html', {
            'etudiant': etudiant, 'cgpa': cgpa, 'credits': credits,
            'nb_valid': nb_valid, 'annee': annee, 'menus': menus,
            'compte': compte, 'recentes_notes': recentes_notes, 'nb_ues': nb_ues})
    stats = services.stats_dashboard()
    annee = stats['annee']
    menus = models.MenuJour.objects.filter(date=timezone.now().date()).select_related('plat')
    chiffre_cantine = models.CommandeCantine.objects.filter(annule=False).aggregate(s=Sum('montant'))['s'] or 0
    total_paye = models.Paiement.objects.filter(annee=annee).aggregate(s=Sum('montant'))['s'] or 0
    contexte = {
        'stats': stats,
        'menus': menus,
        'recentes_inscriptions': models.Inscription.objects.select_related('etudiant', 'filiere').order_by('-id')[:8],
        'recentes_notes': models.Note.objects.select_related('etudiant', 'ue').order_by('-id')[:8],
        'comptes_cantine': models.CantineCompte.objects.select_related('etudiant').order_by('-solde')[:5],
        'solde_total': models.CantineCompte.objects.aggregate(s=Sum('solde'))['s'] or 0,
        'chiffre_cantine': chiffre_cantine,
        'total_paye': total_paye,
        'annee': annee,
    }
    return render(request, 'universite/dashboard.html', contexte)


# ---------------------------------------------------------------------------
# Années académiques & semestres
# ---------------------------------------------------------------------------

@consultation_uniquement
def annees(request):
    lecture_seule = not est_personnel(request.user)
    lignes = []
    for a in models.AnneeAcademique.objects.all():
        row = [
            a.libelle,
            a.date_debut.strftime('%d/%m/%Y'),
            a.date_fin.strftime('%d/%m/%Y'),
            _badge('actif' if a.active else 'inactif'),
            a.semestres.count(),
        ]
        if not lecture_seule:
            row += [c('Modifier', url=reverse('universite_annee_update', args=[a.pk])),
                    c('Supprimer', url=reverse('universite_annee_delete', args=[a.pk]))]
        lignes.append(row)
    colonnes = ['Libellé', 'Début', 'Fin', 'Statut', 'Semestres']
    bouton, bouton_url = None, '#'
    if not lecture_seule:
        colonnes += ['', '']
        bouton, bouton_url = 'Nouvelle année', reverse('universite_annee_create')
    contexte = _contexte_liste(
        'Années académiques', 'bi-calendar-range', colonnes, lignes,
        bouton=bouton, bouton_url=bouton_url)
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def annee_create(request):
    form = AnneeAcademiqueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Année académique créée.')
        return redirect('universite_annees')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle année académique', 'icone': 'bi-calendar-range',
        'form': form, 'retour': reverse('universite_annees')})


@personnel_uniquement
def annee_update(request, pk):
    objet = get_object_or_404(models.AnneeAcademique, pk=pk)
    form = AnneeAcademiqueForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Année académique mise à jour.')
        return redirect('universite_annees')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.libelle}', 'icone': 'bi-calendar-range',
        'form': form, 'retour': reverse('universite_annees')})


@personnel_uniquement
def annee_activer(request, pk):
    annee = get_object_or_404(models.AnneeAcademique, pk=pk)
    models.AnneeAcademique.objects.filter(active=True).exclude(pk=annee.pk).update(active=False)
    annee.active = True
    annee.save()
    messages.success(request, f'{annee.libelle} est maintenant l\'année active.')
    return redirect('universite_annees')


@personnel_uniquement
def annee_delete(request, pk):
    objet = get_object_or_404(models.AnneeAcademique, pk=pk)
    if objet.active:
        messages.error(request, 'Impossible de supprimer l\'année académique active.')
        return redirect('universite_annees')
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Année académique supprimée.')
        return redirect('universite_annees')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_annees')})


@consultation_uniquement
def semestres(request):
    lecture_seule = not est_personnel(request.user)
    lignes = []
    for s in models.Semestre.objects.select_related('annee').all():
        row = [
            s.nom,
            s.annee.libelle,
            s.date_debut.strftime('%d/%m/%Y'),
            s.date_fin.strftime('%d/%m/%Y'),
            f'{s.credits} ECTS',
            _badge('cloturée' if s.cloture else 'en_cours'),
        ]
        if not lecture_seule:
            row += [c('Modifier', url=reverse('universite_semestre_update', args=[s.pk])),
                    c('Supprimer', url=reverse('universite_semestre_delete', args=[s.pk]))]
        lignes.append(row)
    colonnes = ['Semestre', 'Année', 'Début', 'Fin', 'Crédits', 'État']
    bouton, bouton_url = None, '#'
    if not lecture_seule:
        colonnes += ['', '']
        bouton, bouton_url = 'Nouveau semestre', reverse('universite_semestre_create')
    contexte = _contexte_liste(
        'Semestres', 'bi-layers', colonnes, lignes,
        bouton=bouton, bouton_url=bouton_url)
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def semestre_create(request):
    form = SemestreForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Semestre créé.')
        return redirect('universite_semestres')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau semestre', 'icone': 'bi-layers',
        'form': form, 'retour': reverse('universite_semestres')})


@personnel_uniquement
def semestre_update(request, pk):
    objet = get_object_or_404(models.Semestre, pk=pk)
    form = SemestreForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Semestre mis à jour.')
        return redirect('universite_semestres')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-layers',
        'form': form, 'retour': reverse('universite_semestres')})


@personnel_uniquement
def semestre_delete(request, pk):
    objet = get_object_or_404(models.Semestre, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Semestre supprimé.')
        return redirect('universite_semestres')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_semestres')})


# ---------------------------------------------------------------------------
# Organisation : facultés, départements, filières, salles
# ---------------------------------------------------------------------------

@consultation_uniquement
def facultes(request):
    lecture_seule = not est_personnel(request.user)
    lignes = []
    for f in models.Faculte.objects.annotate(nb_dep=Count('departements')).all():
        nom = c(f.nom, url=reverse('universite_departements')) if not lecture_seule else f.nom
        row = [
            nom,
            f.code or '—',
            f.doyen or '—',
            nb_dep if (nb_dep := f.nb_dep) else 0,
            f.effectif,
        ]
        if not lecture_seule:
            row += [c('Modifier', url=reverse('universite_faculte_update', args=[f.pk])),
                    c('Supprimer', url=reverse('universite_faculte_delete', args=[f.pk]))]
        lignes.append(row)
    colonnes = ['Faculté', 'Code', 'Doyen', 'Départements', 'Étudiants']
    bouton, bouton_url = None, '#'
    if not lecture_seule:
        colonnes += ['', '']
        bouton, bouton_url = 'Nouvelle faculté', reverse('universite_faculte_create')
    contexte = _contexte_liste(
        'Facultés', 'bi-building', colonnes, lignes,
        bouton=bouton, bouton_url=bouton_url)
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def faculte_create(request):
    form = FaculteForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Faculté créée.')
        return redirect('universite_facultes')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle faculté', 'icone': 'bi-building',
        'form': form, 'retour': reverse('universite_facultes')})


@personnel_uniquement
def faculte_update(request, pk):
    objet = get_object_or_404(models.Faculte, pk=pk)
    form = FaculteForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Faculté mise à jour.')
        return redirect('universite_facultes')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-building',
        'form': form, 'retour': reverse('universite_facultes')})


@personnel_uniquement
def faculte_delete(request, pk):
    objet = get_object_or_404(models.Faculte, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Faculté supprimée.')
        return redirect('universite_facultes')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_facultes')})


@consultation_uniquement
def departements(request):
    lecture_seule = not est_personnel(request.user)
    lignes = []
    for d in models.Departement.objects.select_related('faculte').annotate(nb_fil=Count('filieres')).all():
        nom = c(d.nom, url=reverse('universite_filieres')) if not lecture_seule else d.nom
        row = [
            nom,
            d.faculte.nom,
            d.code or '—',
            d.chef or '—',
            d.nb_fil,
        ]
        if not lecture_seule:
            row += [c('Modifier', url=reverse('universite_departement_update', args=[d.pk])),
                    c('Supprimer', url=reverse('universite_departement_delete', args=[d.pk]))]
        lignes.append(row)
    colonnes = ['Département', 'Faculté', 'Code', 'Chef', 'Filières']
    bouton, bouton_url = None, '#'
    if not lecture_seule:
        colonnes += ['', '']
        bouton, bouton_url = 'Nouveau département', reverse('universite_departement_create')
    contexte = _contexte_liste(
        'Départements', 'bi-diagram-3', colonnes, lignes,
        bouton=bouton, bouton_url=bouton_url)
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def departement_create(request):
    form = DepartementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Département créé.')
        return redirect('universite_departements')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau département', 'icone': 'bi-diagram-3',
        'form': form, 'retour': reverse('universite_departements')})


@personnel_uniquement
def departement_update(request, pk):
    objet = get_object_or_404(models.Departement, pk=pk)
    form = DepartementForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Département mis à jour.')
        return redirect('universite_departements')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-diagram-3',
        'form': form, 'retour': reverse('universite_departements')})


@personnel_uniquement
def departement_delete(request, pk):
    objet = get_object_or_404(models.Departement, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Département supprimé.')
        return redirect('universite_departements')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_departements')})


@consultation_uniquement
def filieres(request):
    lecture_seule = not est_personnel(request.user)
    lignes = []
    for f in models.Filiere.objects.select_related('departement').all():
        nom = c(f.nom, url=reverse('universite_filiere_detail', args=[f.pk])) if not lecture_seule else f.nom
        row = [
            nom,
            f.code or '—',
            f.departement.faculte.nom,
            f.departement.nom,
            f.niveau,
            f.effectif,
        ]
        if not lecture_seule:
            row += [c('Détails', url=reverse('universite_filiere_detail', args=[f.pk])),
                    c('Modifier', url=reverse('universite_filiere_update', args=[f.pk])),
                    c('Supprimer', url=reverse('universite_filiere_delete', args=[f.pk]))]
        lignes.append(row)
    colonnes = ['Filière', 'Code', 'Faculté', 'Département', 'Niveau', 'Étudiants']
    bouton, bouton_url = None, '#'
    if not lecture_seule:
        colonnes += ['', '', '']
        bouton, bouton_url = 'Nouvelle filière', reverse('universite_filiere_create')
    contexte = _contexte_liste(
        'Filières / Programmes', 'bi-mortarboard', colonnes, lignes,
        bouton=bouton, bouton_url=bouton_url)
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def filiere_create(request):
    form = FiliereForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Filière créée.')
        return redirect('universite_filieres')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle filière', 'icone': 'bi-mortarboard',
        'form': form, 'retour': reverse('universite_filieres')})


@personnel_uniquement
def filiere_update(request, pk):
    objet = get_object_or_404(models.Filiere, pk=pk)
    form = FiliereForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Filière mise à jour.')
        return redirect('universite_filiere_detail', pk=objet.pk)
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-mortarboard',
        'form': form, 'retour': reverse('universite_filiere_detail', args=[objet.pk])})


@personnel_uniquement
def filiere_delete(request, pk):
    objet = get_object_or_404(models.Filiere, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Filière supprimée.')
        return redirect('universite_filieres')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_filieres')})


@personnel_uniquement
def filiere_detail(request, pk):
    filiere = get_object_or_404(models.Filiere.objects.select_related('departement', 'departement__faculte'), pk=pk)
    ues = filiere.ues.select_related('semestre').order_by('semestre', 'code')
    inscriptions = filiere.inscriptions.filter(statut='active').select_related('etudiant')[:20]
    return render(request, 'universite/filiere/detail.html', {
        'filiere': filiere, 'ues': ues, 'inscriptions': inscriptions})


@personnel_uniquement
def salles(request):
    lignes = []
    for s in models.Salle.objects.all():
        lignes.append([
            s.nom, s.get_type_display(), s.capacite, s.equipement or '—',
            c('Modifier', url=reverse('universite_salle_update', args=[s.pk])),
            c('Supprimer', url=reverse('universite_salle_delete', args=[s.pk])),
        ])
    contexte = _contexte_liste(
        'Salles', 'bi-door-open', ['Salle', 'Type', 'Capacité', 'Équipement', '', ''],
        lignes, bouton='Nouvelle salle', bouton_url=reverse('universite_salle_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def salle_create(request):
    form = SalleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Salle créée.')
        return redirect('universite_salles')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle salle', 'icone': 'bi-door-open',
        'form': form, 'retour': reverse('universite_salles')})


@personnel_uniquement
def salle_update(request, pk):
    objet = get_object_or_404(models.Salle, pk=pk)
    form = SalleForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Salle mise à jour.')
        return redirect('universite_salles')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-door-open',
        'form': form, 'retour': reverse('universite_salles')})


@personnel_uniquement
def salle_delete(request, pk):
    objet = get_object_or_404(models.Salle, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Salle supprimée.')
        return redirect('universite_salles')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_salles')})


# ---------------------------------------------------------------------------
# Enseignants
# ---------------------------------------------------------------------------

@personnel_uniquement
def enseignants(request):
    lignes = []
    for e in models.Enseignant.objects.select_related('departement').all():
        lignes.append([
            c(f'{e.nom} {e.prenom}', url=reverse('universite_enseignant_update', args=[e.pk])),
            e.matricule, e.grade,
            e.departement.nom if e.departement else '—',
            e.telephone or '—', _badge(e.statut),
        ])
    contexte = _contexte_liste(
        'Enseignants & chercheurs', 'bi-people', ['Nom', 'Matricule', 'Grade', 'Département', 'Téléphone', 'Statut'],
        lignes, bouton='Nouvel enseignant', bouton_url=reverse('universite_enseignant_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def enseignant_create(request):
    form = EnseignantForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Enseignant ajouté.')
        return redirect('universite_enseignants')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvel enseignant', 'icone': 'bi-person-plus',
        'form': form, 'retour': reverse('universite_enseignants')})


@personnel_uniquement
def enseignant_update(request, pk):
    objet = get_object_or_404(models.Enseignant, pk=pk)
    form = EnseignantForm(request.POST or None, request.FILES or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Enseignant mis à jour.')
        return redirect('universite_enseignants')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom_complet}', 'icone': 'bi-person-gear',
        'form': form, 'retour': reverse('universite_enseignants')})


@personnel_uniquement
def enseignant_delete(request, pk):
    objet = get_object_or_404(models.Enseignant, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Enseignant supprimé.')
        return redirect('universite_enseignants')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_enseignants')})


# ---------------------------------------------------------------------------
# Étudiants
# ---------------------------------------------------------------------------

@personnel_uniquement
def etudiants(request):
    filtre = request.GET.get('q', '').strip()
    filiere_id = request.GET.get('filiere', '')
    qs = models.Etudiant.objects.select_related('filiere').all()
    if filtre:
        qs = qs.filter(nom__icontains=filtre) | qs.filter(prenom__icontains=filtre) | \
             qs.filter(matricule__icontains=filtre)
    if filiere_id:
        qs = qs.filter(filiere_id=filiere_id)
    lignes = []
    for e in qs:
        moy = services.moyenne_etudiant(e)
        lignes.append([
            c(f'{e.nom} {e.prenom}', url=reverse('universite_etudiant_detail', args=[e.pk])),
            e.matricule,
            e.filiere.nom if e.filiere else '—',
            'M' if e.sexe == 'M' else 'F',
            e.telephone or '—',
            f'{moy}/20',
            _badge(e.statut),
        ])
    contexte = _contexte_liste(
        'Étudiants', 'bi-person-video2', ['Nom', 'Matricule', 'Filière', 'Sexe', 'Téléphone', 'Moyenne', 'Statut'],
        lignes, bouton='Nouvel étudiant', bouton_url=reverse('universite_etudiant_create'))
    contexte['filieres'] = models.Filiere.objects.all()
    contexte['recherche'] = filtre
    contexte['filiere_sel'] = filiere_id
    return render(request, 'universite/etudiant/liste.html', contexte)


@personnel_uniquement
def etudiant_create(request):
    form = EtudiantForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        etudiant = form.save()
        messages.success(request, f'Étudiant {etudiant.matricule} créé.')
        return redirect('universite_etudiants')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvel étudiant', 'icone': 'bi-person-plus',
        'form': form, 'retour': reverse('universite_etudiants')})


@personnel_uniquement
def etudiant_detail(request, pk):
    etudiant = get_object_or_404(models.Etudiant.objects.select_related('filiere'), pk=pk)
    inscriptions = etudiant.inscriptions.select_related('annee', 'filiere').order_by('-annee')
    paiements = etudiant.paiements.select_related('type_frais').order_by('-date')[:10]
    cgpa, credits, nb_valid = services.cgpa_etudiant(etudiant)
    note_totale, note_moy = services.moyenne_etudiant(etudiant), None
    compte = getattr(etudiant, 'cantine', None)
    validations = etudiant.validations.select_related('ue').order_by('semestre', 'ue')
    return render(request, 'universite/etudiant/detail.html', {
        'etudiant': etudiant, 'inscriptions': inscriptions, 'paiements': paiements,
        'cgpa': cgpa, 'credits': credits, 'nb_valid': nb_valid,
        'moyenne': services.moyenne_etudiant(etudiant),
        'compte': compte, 'validations': validations})


@personnel_uniquement
def etudiant_update(request, pk):
    objet = get_object_or_404(models.Etudiant, pk=pk)
    form = EtudiantForm(request.POST or None, request.FILES or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Étudiant mis à jour.')
        return redirect('universite_etudiant_detail', pk=objet.pk)
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom_complet}', 'icone': 'bi-person-gear',
        'form': form, 'retour': reverse('universite_etudiant_detail', args=[objet.pk])})


@personnel_uniquement
def etudiant_delete(request, pk):
    objet = get_object_or_404(models.Etudiant, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Étudiant supprimé.')
        return redirect('universite_etudiants')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_etudiants')})


@personnel_uniquement
def export_etudiants(request):
    reponse = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    reponse['Content-Disposition'] = 'attachment; filename="etudiants.csv"'
    ecrivain = csv.writer(reponse, delimiter=';')
    ecrivain.writerow(['Matricule', 'Nom', 'Prénom', 'Sexe', 'Naissance', 'Téléphone',
                       'Email', 'Filière', 'Statut'])
    for e in models.Etudiant.objects.select_related('filiere').all():
        ecrivain.writerow([e.matricule, e.nom, e.prenom, e.sexe,
                           e.date_naissance.strftime('%d/%m/%Y'),
                           e.telephone, e.email,
                           e.filiere.nom if e.filiere else '', e.statut])
    return reponse


# ---------------------------------------------------------------------------
# Inscriptions
# ---------------------------------------------------------------------------

@personnel_uniquement
def inscriptions(request):
    annee = models.AnneeAcademique.en_cours()
    lignes = []
    qs = models.Inscription.objects.select_related('etudiant', 'annee', 'filiere') \
        .filter(annee=annee).order_by('-date')
    for ins in qs:
        lignes.append([
            c(ins.numero, url=reverse('universite_inscription_detail', args=[ins.pk])),
            c(f'{ins.etudiant.nom} {ins.etudiant.prenom}', url=reverse('universite_etudiant_detail', args=[ins.etudiant.pk])),
            ins.etudiant.matricule,
            ins.filiere.nom,
            f'L{ins.niveau_annee}',
            ins.date.strftime('%d/%m/%Y'),
            _badge(ins.statut),
        ])
    contexte = _contexte_liste(
        f'Inscriptions — {annee.libelle}', 'bi-clipboard-check',
        ['N°', 'Étudiant', 'Matricule', 'Filière', 'Niveau', 'Date', 'Statut'],
        lignes, bouton='Nouvelle inscription', bouton_url=reverse('universite_inscription_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def inscription_create(request):
    form = InscriptionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Inscription enregistrée.')
        return redirect('universite_inscriptions')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle inscription', 'icone': 'bi-clipboard-check',
        'form': form, 'retour': reverse('universite_inscriptions')})


@personnel_uniquement
def inscription_detail(request, pk):
    ins = get_object_or_404(models.Inscription.objects.select_related('etudiant', 'annee', 'filiere'), pk=pk)
    paiements = ins.etudiant.paiements.filter(annee=ins.annee).select_related('type_frais')
    total_paye = paiements.aggregate(s=Sum('montant'))['s'] or 0
    return render(request, 'universite/inscription/detail.html', {
        'ins': ins, 'paiements': paiements, 'total_paye': total_paye})


# ---------------------------------------------------------------------------
# Unités d'enseignement (UE)
# ---------------------------------------------------------------------------

@consultation_uniquement
def ues(request):
    lecture_seule = not est_personnel(request.user)
    qs = models.UniteEnseignement.objects.select_related('filiere', 'semestre')
    if lecture_seule and est_etudiant(request.user):
        filiere = request.user.etudiant.filiere
        qs = qs.filter(filiere=filiere) if filiere else qs.none()
    lignes = []
    for ue in qs:
        resp = ue.responsable
        code = c(ue.code, url=reverse('universite_ue_detail', args=[ue.pk])) if not lecture_seule else ue.code
        row = [
            code,
            ue.nom,
            ue.filiere.nom,
            ue.semestre.nom,
            f'{ue.credits} ECTS',
            resp.nom_complet if resp else '—',
        ]
        if not lecture_seule:
            row += [c('Modifier', url=reverse('universite_ue_update', args=[ue.pk])),
                    c('Supprimer', url=reverse('universite_ue_delete', args=[ue.pk]))]
        lignes.append(row)
    colonnes = ['Code', 'Intitulé', 'Filière', 'Semestre', 'Crédits', 'Responsable']
    bouton, bouton_url = None, '#'
    if not lecture_seule:
        colonnes += ['', '']
        bouton, bouton_url = 'Nouvelle UE', reverse('universite_ue_create')
    contexte = _contexte_liste(
        'Unités d\'enseignement (UE)', 'bi-journal-bookmark', colonnes, lignes,
        bouton=bouton, bouton_url=bouton_url)
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def ue_create(request):
    form = UeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'UE créée.')
        return redirect('universite_ues')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle UE', 'icone': 'bi-journal-plus',
        'form': form, 'retour': reverse('universite_ues')})


@personnel_uniquement
def ue_update(request, pk):
    objet = get_object_or_404(models.UniteEnseignement, pk=pk)
    form = UeForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'UE mise à jour.')
        return redirect('universite_ue_detail', pk=objet.pk)
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.code}', 'icone': 'bi-journal-bookmark',
        'form': form, 'retour': reverse('universite_ue_detail', args=[objet.pk])})


@personnel_uniquement
def ue_delete(request, pk):
    objet = get_object_or_404(models.UniteEnseignement, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'UE supprimée.')
        return redirect('universite_ues')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_ues')})


@personnel_uniquement
def ue_detail(request, pk):
    ue = get_object_or_404(models.UniteEnseignement.objects.select_related('filiere', 'semestre'), pk=pk)
    affectations = ue.affectations.select_related('enseignant')
    creneaux = ue.creneaux.select_related('salle').order_by('jour', 'heure_debut')
    dernieres_notes = ue.notes.select_related('etudiant').order_by('-date')[:12]
    return render(request, 'universite/ue/detail.html', {
        'ue': ue, 'affectations': affectations, 'creneaux': creneaux,
        'dernieres_notes': dernieres_notes})


@personnel_uniquement
def affectations(request):
    lignes = []
    for a in models.AffectationUE.objects.select_related('ue', 'enseignant').all():
        lignes.append([
            a.ue.code, a.ue.nom, a.enseignant.nom_complet,
            f'{a.heures_cours}+{a.heures_td}+{a.heures_tp}',
            f'{a.total_heures} h',
            c('Modifier', url=reverse('universite_affectation_update', args=[a.pk])),
            c('Supprimer', url=reverse('universite_affectation_delete', args=[a.pk])),
        ])
    contexte = _contexte_liste(
        'Affectations d\'UE', 'bi-diagram-3', ['Code UE', 'Intitulé', 'Enseignant', 'C+TD+TP', 'Total', '', ''],
        lignes, bouton='Nouvelle affectation', bouton_url=reverse('universite_affectation_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def affectation_create(request):
    form = AffectationUEForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Affectation enregistrée.')
        return redirect('universite_affectations')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle affectation', 'icone': 'bi-diagram-3',
        'form': form, 'retour': reverse('universite_affectations')})


@personnel_uniquement
def affectation_update(request, pk):
    objet = get_object_or_404(models.AffectationUE, pk=pk)
    form = AffectationUEForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Affectation mise à jour.')
        return redirect('universite_affectations')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Modifier une affectation', 'icone': 'bi-diagram-3',
        'form': form, 'retour': reverse('universite_affectations')})


@personnel_uniquement
def affectation_delete(request, pk):
    objet = get_object_or_404(models.AffectationUE, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Affectation supprimée.')
        return redirect('universite_affectations')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_affectations')})


# ---------------------------------------------------------------------------
# Notes & relevés
# ---------------------------------------------------------------------------

@consultation_uniquement
def notes(request):
    lecture_seule = not est_personnel(request.user)
    ue_id = request.GET.get('ue', '')
    etu_id = request.GET.get('etudiant', '')
    qs = models.Note.objects.select_related('etudiant', 'ue').order_by('-date')
    if lecture_seule and est_etudiant(request.user):
        qs = qs.filter(etudiant=request.user.etudiant)
    if ue_id:
        qs = qs.filter(ue_id=ue_id)
    if etu_id:
        qs = qs.filter(etudiant_id=etu_id)
    lignes = []
    for n in qs[:200]:
        etudiant = c(f'{n.etudiant.nom} {n.etudiant.prenom}',
                     url=reverse('universite_etudiant_detail', args=[n.etudiant.pk])) if not lecture_seule else f'{n.etudiant.nom} {n.etudiant.prenom}'
        row = [
            etudiant,
            n.ue.code,
            n.get_type_display(),
            c(f'{n.note}/20', badge='success' if float(n.note) >= 10 else 'danger'),
            n.apprecie,
            n.date.strftime('%d/%m/%Y'),
        ]
        if not lecture_seule:
            row.append(c('Supprimer', url=reverse('universite_note_delete', args=[n.pk])))
        lignes.append(row)
    colonnes = ['Étudiant', 'UE', 'Type', 'Note', 'Appréciation', 'Date']
    bouton, bouton_url = None, '#'
    if not lecture_seule:
        colonnes.append('Actions')
        bouton, bouton_url = 'Saisie des notes', reverse('universite_saisie_notes')
    contexte = _contexte_liste(
        'Notes', 'bi-pencil-square', colonnes, lignes,
        bouton=bouton, bouton_url=bouton_url)
    contexte['ues'] = models.UniteEnseignement.objects.all()
    contexte['ue_sel'] = ue_id
    contexte['etudiants'] = models.Etudiant.objects.all()
    contexte['etu_sel'] = etu_id
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/note/liste.html', contexte)


@personnel_uniquement
def saisie_notes(request):
    if request.method == 'POST':
        ue = get_object_or_404(models.UniteEnseignement, pk=request.POST.get('ue'))
        date = request.POST.get('date') or timezone.now().date()
        type_note = request.POST.get('type', 'EX')
        nb = 0
        for cle, valeur in request.POST.items():
            if cle.startswith('note_') and valeur.strip():
                etudiant_id = cle.split('_', 1)[1]
                note_val = valeur.replace(',', '.')
                try:
                    note_val = float(note_val)
                    if 0 <= note_val <= 20:
                        models.Note.objects.update_or_create(
                            etudiant_id=etudiant_id, ue=ue, type=type_note, date=date,
                            defaults={'note': note_val})
                        nb += 1
                except ValueError:
                    continue
        messages.success(request, f'{nb} note(s) enregistrée(s) pour {ue.code}.')
        return redirect('universite_notes')
    ue_id = request.GET.get('ue', '')
    etudiants = []
    ue = None
    if ue_id:
        ue = get_object_or_404(models.UniteEnseignement.objects.select_related('filiere'), pk=ue_id)
        etudiants = models.Etudiant.objects.filter(filiere=ue.filiere, statut='actif')
    return render(request, 'universite/note/saisie.html', {
        'ues': models.UniteEnseignement.objects.all(), 'ue': ue,
        'ue_id': ue_id, 'etudiants': etudiants,
        'ue_note_types': models.Note.TYPES})


@personnel_uniquement
def note_delete(request, pk):
    objet = get_object_or_404(models.Note, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Note supprimée.')
        return redirect('universite_notes')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_notes')})


@personnel_uniquement
def releves(request):
    lignes = []
    for e in models.Etudiant.objects.select_related('filiere').filter(statut='actif'):
        cgpa, credits, nb_valid = services.cgpa_etudiant(e)
        lignes.append([
            c(f'{e.nom} {e.prenom}', url=reverse('universite_releve_etudiant', args=[e.pk])),
            e.matricule,
            e.filiere.nom if e.filiere else '—',
            f'{nb_valid} UE',
            f'{credits} ECTS',
            c(f'{cgpa}/20', badge='success' if cgpa >= 10 else 'warning'),
        ])
    contexte = _contexte_liste(
        'Relevés de notes (LMD)', 'bi-file-earmark-text',
        ['Étudiant', 'Matricule', 'Filière', 'UE validées', 'Crédits', 'CGPA'],
        lignes)
    return render(request, 'universite/partials/liste.html', contexte)


@consultation_uniquement
def releve_etudiant(request, pk):
    etudiant = get_object_or_404(models.Etudiant.objects.select_related('filiere'), pk=pk)
    if not est_personnel(request.user):
        if not hasattr(request.user, 'etudiant') or request.user.etudiant.pk != etudiant.pk:
            messages.warning(request, 'Vous ne pouvez consulter que votre propre bulletin.')
            return redirect('universite_releve_etudiant', pk=request.user.etudiant.pk)
    cgpa, credits, nb_valid = services.cgpa_etudiant(etudiant)
    semestres = []
    for sem in models.Semestre.objects.select_related('annee').order_by('annee', 'type'):
        ligne_sem = []
        total_notes, total_credits, notes_sem = [], 0, []
        for ue in sem.ues.filter(filiere=etudiant.filiere):
            moyenne = services.moyenne_ue(etudiant, ue)
            valid = models.ValidationUE.objects.filter(etudiant=etudiant, ue=ue, semestre=sem).first()
            ligne_sem.append({'ue': ue, 'moyenne': moyenne, 'decision': valid})
            if moyenne is not None:
                notes_sem.append(moyenne)
        moy_sem = None
        if notes_sem:
            moy_sem = (sum(notes_sem) / len(notes_sem)).quantize(Decimal('0.01'))
        if ligne_sem:
            semestres.append({'semestre': sem, 'lignes': ligne_sem, 'moyenne': moy_sem})
    return render(request, 'universite/releve/releve.html', {
        'etudiant': etudiant, 'cgpa': cgpa, 'credits': credits, 'nb_valid': nb_valid,
        'semestres': semestres})


@personnel_uniquement
def deliberer(request):
    if request.method == 'POST':
        semestre = get_object_or_404(models.Semestre, pk=request.POST.get('semestre'))
        filiere = get_object_or_404(models.Filiere, pk=request.POST.get('filiere'))
        etudiants = models.Inscription.objects.filter(filiere=filiere, annee=semestre.annee,
                                                      statut='active').values_list('etudiant_id', flat=True)
        total = 0
        for eid in etudiants:
            etudiant = models.Etudiant.objects.get(pk=eid)
            validations = services.decider_ues(etudiant, semestre)
            total += len(validations)
        messages.success(request, f'Délibération effectuée : {total} décision(s) pour {filiere.nom}.')
        return redirect('universite_deliberer')
    return render(request, 'universite/releve/deliberer.html', {
        'semestres': models.Semestre.objects.select_related('annee').order_by('-id'),
        'filieres': models.Filiere.objects.all()})


# ---------------------------------------------------------------------------
# Présences
# ---------------------------------------------------------------------------

@personnel_uniquement
def presences(request):
    ue_id = request.GET.get('ue', '')
    qs = models.Presence.objects.select_related('etudiant', 'ue').order_by('-date')
    if ue_id:
        qs = qs.filter(ue_id=ue_id)
    lignes = []
    for p in qs[:150]:
        lignes.append([
            c(f'{p.etudiant.nom} {p.etudiant.prenom}', url=reverse('universite_etudiant_detail', args=[p.etudiant.pk])),
            p.ue.code,
            p.date.strftime('%d/%m/%Y'),
            _badge(p.statut),
            p.justificatif or '—',
            c('Supprimer', url=reverse('universite_presence_delete', args=[p.pk])),
        ])
    contexte = _contexte_liste(
        'Présences', 'bi-calendar-check', ['Étudiant', 'UE', 'Date', 'Statut', 'Justificatif', 'Actions'],
        lignes, bouton='Appel', bouton_url=reverse('universite_appel'))
    contexte['ues'] = models.UniteEnseignement.objects.all()
    contexte['ue_sel'] = ue_id
    return render(request, 'universite/presence/liste.html', contexte)


@personnel_uniquement
def presence_delete(request, pk):
    objet = get_object_or_404(models.Presence, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Présence supprimée.')
        return redirect('universite_presences')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_presences')})


@personnel_uniquement
def appel(request):
    if request.method == 'POST':
        ue = get_object_or_404(models.UniteEnseignement, pk=request.POST.get('ue'))
        date = request.POST.get('date') or timezone.now().date()
        nb = 0
        for cle, valeur in request.POST.items():
            if cle.startswith('presence_'):
                etudiant_id = cle.split('_', 1)[1]
                statut = valeur
                heure = request.POST.get(f'heure_{etudiant_id}') or None
                models.Presence.objects.update_or_create(
                    etudiant_id=etudiant_id, ue=ue, date=date,
                    defaults={'statut': statut, 'heure_arrivee': heure})
                nb += 1
        messages.success(request, f'Appel enregistré pour {ue.code} ({nb} étudiant(s)).')
        return redirect('universite_presences')
    ue_id = request.GET.get('ue', '')
    ues = models.UniteEnseignement.objects.all()
    etudiants = []
    ue = None
    if ue_id:
        ue = get_object_or_404(models.UniteEnseignement.objects.select_related('filiere'), pk=ue_id)
        etudiants = models.Etudiant.objects.filter(filiere=ue.filiere, statut='actif')
    return render(request, 'universite/presence/appel.html', {
        'ues': ues, 'ue_id': ue_id, 'etudiants': etudiants, 'ue': ue})


# ---------------------------------------------------------------------------
# Emploi du temps
# ---------------------------------------------------------------------------

@personnel_uniquement
def emplois(request):
    jour = request.GET.get('jour', '')
    jours = ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi']
    creneaux = models.Creneau.objects.select_related('ue', 'salle').order_by('jour', 'heure_debut')
    if jour:
        creneaux = creneaux.filter(jour=jour)
    lignes = []
    for cr in creneaux:
        lignes.append([
            cr.jour,
            f'{cr.heure_debut:%H:%M} - {cr.heure_fin:%H:%M}',
            f'{cr.ue.code} — {cr.ue.nom}',
            cr.get_type_display(),
            cr.salle.nom if cr.salle else '—',
            cr.ue.responsable.nom_complet if cr.ue.responsable else '—',
            c('Supprimer', url=reverse('universite_emploi_delete', args=[cr.pk])),
        ])
    contexte = _contexte_liste(
        'Emploi du temps', 'bi-calendar-week', ['Jour', 'Heures', 'UE', 'Type', 'Salle', 'Enseignant', 'Actions'],
        lignes, bouton='Nouveau créneau', bouton_url=reverse('universite_emploi_create'))
    contexte['jours'] = jours
    contexte['jour_sel'] = jour
    return render(request, 'universite/emploi/liste.html', contexte)


@personnel_uniquement
def emploi_create(request):
    form = CreneauForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Créneau ajouté à l\'emploi du temps.')
        return redirect('universite_emplois')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau créneau', 'icone': 'bi-calendar-plus',
        'form': form, 'retour': reverse('universite_emplois')})


@personnel_uniquement
def emploi_delete(request, pk):
    objet = get_object_or_404(models.Creneau, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Créneau supprimé.')
        return redirect('universite_emplois')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_emplois')})


# ---------------------------------------------------------------------------
# Examens
# ---------------------------------------------------------------------------

@personnel_uniquement
def examens(request):
    lignes = []
    for ex in models.Examen.objects.select_related('annee').all():
        lignes.append([
            c(ex.nom, url=reverse('universite_examen_detail', args=[ex.pk])),
            ex.annee.libelle, ex.get_session_display(),
            ex.date_debut.strftime('%d/%m/%Y'),
            ex.epreuves.count(),
            _badge(ex.statut),
            c('Modifier', url=reverse('universite_examen_update', args=[ex.pk])),
            c('Supprimer', url=reverse('universite_examen_delete', args=[ex.pk])),
        ])
    contexte = _contexte_liste(
        'Examens & sessions', 'bi-award', ['Examen', 'Année', 'Session', 'Début', 'Épreuves', 'Statut', '', ''],
        lignes, bouton='Nouvel examen', bouton_url=reverse('universite_examen_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def examen_create(request):
    form = ExamenForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Examen créé.')
        return redirect('universite_examens')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvel examen', 'icone': 'bi-award',
        'form': form, 'retour': reverse('universite_examens')})


@personnel_uniquement
def examen_update(request, pk):
    objet = get_object_or_404(models.Examen, pk=pk)
    form = ExamenForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Examen mis à jour.')
        return redirect('universite_examen_detail', pk=objet.pk)
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-award',
        'form': form, 'retour': reverse('universite_examen_detail', args=[objet.pk])})


@personnel_uniquement
def examen_delete(request, pk):
    objet = get_object_or_404(models.Examen, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Examen supprimé.')
        return redirect('universite_examens')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_examens')})


@personnel_uniquement
def examen_detail(request, pk):
    examen = get_object_or_404(models.Examen.objects.select_related('annee'), pk=pk)
    epreuves = examen.epreuves.select_related('ue', 'salle').order_by('date', 'heure_debut')
    return render(request, 'universite/examen/detail.html', {
        'examen': examen, 'epreuves': epreuves})


@personnel_uniquement
def epreuve_create(request, examen_pk):
    examen = get_object_or_404(models.Examen, pk=examen_pk)
    form = EpreuveExamenForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        epreuve = form.save(commit=False)
        epreuve.examen = examen
        epreuve.save()
        form.save_m2m()
        messages.success(request, 'Épreuve ajoutée.')
        return redirect('universite_examen_detail', pk=examen.pk)
    return render(request, 'universite/partials/form.html', {
        'titre': f'Ajouter une épreuve — {examen.nom}', 'icone': 'bi-journal-plus',
        'form': form, 'retour': reverse('universite_examen_detail', args=[examen.pk])})


@personnel_uniquement
def epreuve_convoquer(request, epreuve_pk):
    epreuve = get_object_or_404(models.EpreuveExamen.objects.select_related('ue', 'examen'), pk=epreuve_pk)
    if request.method == 'POST':
        present = request.POST.get('present', 'off') == 'on'
        note = request.POST.get('note') or None
        models.Convocation.objects.update_or_create(
            epreuve=epreuve, etudiant_id=request.POST.get('etudiant'),
            defaults={'present': present, 'note_epreuve': note})
        messages.success(request, 'Convocation mise à jour.')
        return redirect('universite_epreuve_convoquer', epreuve_pk=epreuve.pk)
    etudiants = models.Etudiant.objects.filter(filiere=epreuve.ue.filiere, statut='actif')
    convos = {cv.etudiant_id: cv for cv in epreuve.convocations.select_related('etudiant')}
    return render(request, 'universite/examen/convoquer.html', {
        'epreuve': epreuve, 'etudiants': etudiants, 'convos': convos})


@personnel_uniquement
def epreuve_delete(request, pk):
    epreuve = get_object_or_404(models.EpreuveExamen, pk=pk)
    examen_pk = epreuve.examen.pk
    if request.method == 'POST':
        epreuve.delete()
        messages.success(request, 'Épreuve supprimée.')
        return redirect('universite_examen_detail', pk=examen_pk)
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(epreuve), 'retour': reverse('universite_examen_detail', args=[examen_pk])})


# ---------------------------------------------------------------------------
# Cours en ligne
# ---------------------------------------------------------------------------

@personnel_uniquement
def cours_en_ligne(request):
    lignes = []
    for cours in models.CoursEnLigne.objects.select_related('ue', 'enseignant').all():
        lignes.append([
            c(cours.titre, url=reverse('universite_cours_detail', args=[cours.pk])),
            cours.ue.code,
            cours.enseignant.nom_complet if cours.enseignant else '—',
            f'{cours.duree_minutes} min',
            _badge('Publié' if cours.publie else 'Brouillon'),
            c('Modifier', url=reverse('universite_cours_update', args=[cours.pk])),
            c('Supprimer', url=reverse('universite_cours_delete', args=[cours.pk])),
        ])
    contexte = _contexte_liste(
        'Cours en ligne', 'bi-play-circle',
        ['Cours', 'UE', 'Enseignant', 'Durée', 'Statut', 'Modifier', 'Supprimer'],
        lignes, bouton='Nouveau cours', bouton_url=reverse('universite_cours_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def cours_en_ligne_create(request):
    form = CoursEnLigneForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cours en ligne ajouté.')
        return redirect('universite_cours')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau cours en ligne', 'icone': 'bi-play-circle',
        'form': form, 'retour': reverse('universite_cours')})


@personnel_uniquement
def cours_en_ligne_detail(request, pk):
    cours = get_object_or_404(models.CoursEnLigne.objects.select_related('ue', 'enseignant'), pk=pk)
    return render(request, 'universite/cours/detail.html', {'cours': cours})


@personnel_uniquement
def cours_en_ligne_update(request, pk):
    objet = get_object_or_404(models.CoursEnLigne, pk=pk)
    form = CoursEnLigneForm(request.POST or None, request.FILES or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Cours en ligne mis à jour.')
        return redirect('universite_cours_detail', pk=objet.pk)
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier — {objet.titre}', 'icone': 'bi-play-circle',
        'form': form, 'retour': reverse('universite_cours_detail', args=[objet.pk])})


@personnel_uniquement
def cours_en_ligne_delete(request, pk):
    objet = get_object_or_404(models.CoursEnLigne, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Cours en ligne supprimé.')
        return redirect('universite_cours')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_cours')})


# ---------------------------------------------------------------------------
# Scolarité : frais, paiements, bourses
# ---------------------------------------------------------------------------

@personnel_uniquement
def paiements(request):
    annee = models.AnneeAcademique.en_cours()
    lignes = []
    total = 0
    for p in models.Paiement.objects.select_related('etudiant', 'type_frais') \
            .filter(annee=annee).order_by('-date'):
        total += p.montant
        lignes.append([
            p.reference,
            c(f'{p.etudiant.nom} {p.etudiant.prenom}', url=reverse('universite_etudiant_detail', args=[p.etudiant.pk])),
            p.type_frais.nom,
            f'{p.montant:,.0f}',
            p.date.strftime('%d/%m/%Y'),
            p.mode,
            c('Reçu', url=reverse('universite_paiement_recu', args=[p.pk])),
            c('Supprimer', url=reverse('universite_paiement_delete', args=[p.pk])),
        ])
    contexte = _contexte_liste(
        f'Paiements — {annee.libelle}', 'bi-cash-coin',
        ['Référence', 'Étudiant', 'Frais', 'Montant', 'Date', 'Mode', 'Reçu', 'Supprimer'],
        lignes, bouton='Nouveau paiement', bouton_url=reverse('universite_paiement_create'))
    contexte['total'] = total
    contexte['total_formate'] = f'{total:,.0f}'
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def paiement_create(request):
    form = PaiementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        paiement = form.save(commit=False)
        paiement.enregistre_par = request.user
        paiement.save()
        messages.success(request, f'Paiement {paiement.reference} enregistré.')
        return redirect('universite_paiements')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau paiement', 'icone': 'bi-cash-coin',
        'form': form, 'retour': reverse('universite_paiements')})


@personnel_uniquement
def paiement_recu(request, pk):
    paiement = get_object_or_404(models.Paiement.objects.select_related('etudiant', 'type_frais', 'annee'), pk=pk)
    return render(request, 'universite/paiement/recu.html', {
        'paiement': paiement,
        'lettres': services.montant_en_lettres(paiement.montant)})


@personnel_uniquement
def paiement_delete(request, pk):
    objet = get_object_or_404(models.Paiement, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Paiement supprimé.')
        return redirect('universite_paiements')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_paiements')})


@personnel_uniquement
def impayes(request):
    annee = models.AnneeAcademique.en_cours()
    type_inscription = models.TypeFrais.objects.filter(periodicite='inscription').first()
    lignes = []
    for ins in models.Inscription.objects.select_related('etudiant', 'filiere') \
            .filter(annee=annee, statut='active'):
        paye = models.Paiement.objects.filter(etudiant=ins.etudiant, annee=annee) \
            .aggregate(s=Sum('montant'))['s'] or 0
        requis = models.TypeFrais.objects.filter(obligatoire=True).aggregate(s=Sum('montant'))['s'] or 0
        restant = max(requis - paye, 0)
        if restant > 0:
            lignes.append([
                c(f'{ins.etudiant.nom} {ins.etudiant.prenom}', url=reverse('universite_etudiant_detail', args=[ins.etudiant.pk])),
                ins.etudiant.matricule, ins.filiere.nom,
                f'{requis:,.0f}', f'{paye:,.0f}',
                c(f'{restant:,.0f}', badge='danger' if restant > 0 else 'success'),
            ])
    contexte = _contexte_liste(
        f'Étudiants en impayé — {annee.libelle}', 'bi-exclamation-triangle',
        ['Étudiant', 'Matricule', 'Filière', 'Requis', 'Payé', 'Restant'],
        lignes, bouton='Nouveau paiement', bouton_url=reverse('universite_paiement_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def export_paiements(request):
    reponse = HttpResponse(content_type='text/csv; charset=utf-8-sig')
    reponse['Content-Disposition'] = 'attachment; filename="paiements.csv"'
    ecrivain = csv.writer(reponse, delimiter=';')
    ecrivain.writerow(['Référence', 'Étudiant', 'Frais', 'Montant', 'Date', 'Mode'])
    for p in models.Paiement.objects.select_related('etudiant', 'type_frais').all():
        ecrivain.writerow([p.reference, f'{p.etudiant.nom} {p.etudiant.prenom}',
                           p.type_frais.nom, p.montant, p.date.strftime('%d/%m/%Y'), p.mode])
    return reponse


@personnel_uniquement
def types_frais(request):
    lignes = []
    for t in models.TypeFrais.objects.select_related('filiere').all():
        lignes.append([
            t.nom, f'{t.montant:,.0f}', t.get_periodicite_display(),
            _badge('payé' if not t.obligatoire else 'valide'),
            t.filiere.nom if t.filiere else 'Toutes',
            c('Modifier', url=reverse('universite_type_frais_update', args=[t.pk])),
            c('Supprimer', url=reverse('universite_type_frais_delete', args=[t.pk])),
        ])
    contexte = _contexte_liste(
        'Types de frais', 'bi-receipt', ['Intitulé', 'Montant', 'Périodicité', 'Obligatoire', 'Filière', '', ''],
        lignes, bouton='Nouveau frais', bouton_url=reverse('universite_type_frais_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def type_frais_create(request):
    form = TypeFraisForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Type de frais créé.')
        return redirect('universite_types_frais')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau type de frais', 'icone': 'bi-receipt',
        'form': form, 'retour': reverse('universite_types_frais')})


@personnel_uniquement
def type_frais_update(request, pk):
    objet = get_object_or_404(models.TypeFrais, pk=pk)
    form = TypeFraisForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Type de frais mis à jour.')
        return redirect('universite_types_frais')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-receipt',
        'form': form, 'retour': reverse('universite_types_frais')})


@personnel_uniquement
def type_frais_delete(request, pk):
    objet = get_object_or_404(models.TypeFrais, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Type de frais supprimé.')
        return redirect('universite_types_frais')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_types_frais')})


@personnel_uniquement
def bourses(request):
    lignes = []
    for b in models.Bourse.objects.select_related('etudiant').all():
        lignes.append([
            c(f'{b.etudiant.nom} {b.etudiant.prenom}', url=reverse('universite_etudiant_detail', args=[b.etudiant.pk])),
            b.get_type_display(),
            f'{b.montant_mensuel:,.0f}',
            b.date_debut.strftime('%d/%m/%Y'),
            b.date_fin.strftime('%d/%m/%Y') if b.date_fin else '—',
            _badge('actif' if b.actif else 'inactif'),
        ])
    contexte = _contexte_liste(
        'Bourses', 'bi-gem', ['Étudiant', 'Type', 'Montant/mois', 'Début', 'Fin', 'Statut'],
        lignes, bouton='Attribuer une bourse', bouton_url=reverse('universite_bourse_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def bourse_create(request):
    form = BourseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        bourse = form.save()
        bourse.etudiant.boursier = True
        bourse.etudiant.save(update_fields=['boursier'])
        messages.success(request, 'Bourse attribuée.')
        return redirect('universite_bourses')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Attribuer une bourse', 'icone': 'bi-gem',
        'form': form, 'retour': reverse('universite_bourses')})


# ---------------------------------------------------------------------------
# Cantine universitaire
# ---------------------------------------------------------------------------

@consultation_uniquement
def cantine(request):
    aujourdhui = timezone.now().date()
    if est_etudiant(request.user) and not est_personnel(request.user):
        etudiant = request.user.etudiant
        menus = models.MenuJour.objects.filter(date=aujourdhui).select_related('plat')
        plats = models.PlatCantine.objects.filter(actif=True)
        compte = models.CantineCompte.objects.filter(etudiant=etudiant).first()
        commandes = (models.CommandeCantine.objects.filter(compte__etudiant=etudiant, annule=False)
                     .select_related('plat').order_by('-date')[:12])
        return render(request, 'universite/cantine/etudiant.html', {
            'menus': menus, 'plats': plats, 'compte': compte,
            'commandes': commandes, 'aujourdhui': aujourdhui,
            'etudiant': etudiant})
    menus = models.MenuJour.objects.filter(date=aujourdhui).select_related('plat')
    commandes = models.CommandeCantine.objects.filter(annule=False).select_related('compte__etudiant', 'plat')
    chiffre = commandes.aggregate(s=Sum('montant'))['s'] or 0
    nb_commandes = commandes.count()
    comptes = models.CantineCompte.objects.select_related('etudiant')
    solde_total = comptes.aggregate(s=Sum('solde'))['s'] or 0
    par_repas = {}
    for m in models.MenuJour.objects.filter(date=aujourdhui).select_related('plat'):
        par_repas[m.get_type_display()] = m
    return render(request, 'universite/cantine/dashboard.html', {
        'menus': menus, 'commandes': commandes[:12], 'chiffre': chiffre,
        'nb_commandes': nb_commandes, 'comptes': comptes, 'solde_total': solde_total,
        'aujourdhui': aujourdhui})


@personnel_uniquement
def plats(request):
    lignes = []
    for p in models.PlatCantine.objects.all():
        lignes.append([
            c(p.nom, url=reverse('universite_plat_update', args=[p.pk])),
            p.get_categorie_display(),
            f'{p.prix:,.0f}',
            f'{p.calories} kcal',
            f'{p.proteines} P / {p.glucides} G / {p.lipides} L',
            _badge('actif' if p.actif else 'inactif'),
        ])
    contexte = _contexte_liste(
        'Plats de la cantine', 'bi-basket', ['Plat', 'Catégorie', 'Prix', 'Calories', 'Nutrition', 'Statut'],
        lignes, bouton='Nouveau plat', bouton_url=reverse('universite_plat_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def plat_create(request):
    form = PlatCantineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Plat ajouté à la carte.')
        return redirect('universite_plats')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau plat', 'icone': 'bi-basket2',
        'form': form, 'retour': reverse('universite_plats')})


@personnel_uniquement
def plat_update(request, pk):
    objet = get_object_or_404(models.PlatCantine, pk=pk)
    form = PlatCantineForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Plat mis à jour.')
        return redirect('universite_plats')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier {objet.nom}', 'icone': 'bi-basket2',
        'form': form, 'retour': reverse('universite_plats')})


@personnel_uniquement
def plat_delete(request, pk):
    objet = get_object_or_404(models.PlatCantine, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Plat supprimé.')
        return redirect('universite_plats')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_plats')})


@personnel_uniquement
def menus(request):
    lignes = []
    for m in models.MenuJour.objects.select_related('plat').order_by('-date'):
        lignes.append([
            m.date.strftime('%d/%m/%Y'),
            m.get_type_display(),
            m.plat.nom,
            f'{m.plat.prix:,.0f}',
            m.plat.calories,
            c('Modifier', url=reverse('universite_menu_update', args=[m.pk])),
            c('Supprimer', url=reverse('universite_menu_delete', args=[m.pk])),
        ])
    contexte = _contexte_liste(
        'Menus du jour', 'bi-ui-checks', ['Date', 'Repas', 'Plat', 'Prix', 'Calories', '', ''],
        lignes, bouton='Ajouter un menu', bouton_url=reverse('universite_menu_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def menu_create(request):
    form = MenuJourForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Menu ajouté.')
        return redirect('universite_menus')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Ajouter un menu du jour', 'icone': 'bi-ui-checks',
        'form': form, 'retour': reverse('universite_menus')})


@personnel_uniquement
def menu_update(request, pk):
    objet = get_object_or_404(models.MenuJour, pk=pk)
    form = MenuJourForm(request.POST or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Menu mis à jour.')
        return redirect('universite_menus')
    return render(request, 'universite/partials/form.html', {
        'titre': f'Modifier le menu du {objet.date.strftime("%d/%m/%Y")}', 'icone': 'bi-ui-checks',
        'form': form, 'retour': reverse('universite_menus')})


@personnel_uniquement
def menu_delete(request, pk):
    objet = get_object_or_404(models.MenuJour, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Menu supprimé.')
        return redirect('universite_menus')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_menus')})


@personnel_uniquement
def comptes_cantine(request):
    lignes = []
    for cc in models.CantineCompte.objects.select_related('etudiant').order_by('-solde'):
        lignes.append([
            c(f'{cc.etudiant.nom} {cc.etudiant.prenom}', url=reverse('universite_compte_detail', args=[cc.pk])),
            cc.etudiant.matricule,
            cc.code_carte,
            c(f'{cc.solde:,.0f}', badge='success' if cc.solde > 0 else 'danger'),
            cc.recharges.count(),
            _badge('actif' if cc.actif else 'inactif'),
            c('Supprimer', url=reverse('universite_compte_delete', args=[cc.pk])),
        ])
    contexte = _contexte_liste(
        'Comptes cantine', 'bi-wallet2', ['Étudiant', 'Matricule', 'Carte', 'Solde', 'Recharges', 'Statut', 'Actions'],
        lignes, bouton='Ouvrir un compte', bouton_url=reverse('universite_compte_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def compte_delete(request, pk):
    objet = get_object_or_404(models.CantineCompte, pk=pk)
    if request.method == 'POST':
        objet.delete()
        messages.success(request, 'Compte cantine supprimé.')
        return redirect('universite_comptes')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(objet), 'retour': reverse('universite_comptes')})


@personnel_uniquement
def compte_create(request):
    if request.method == 'POST':
        etudiant = get_object_or_404(models.Etudiant, pk=request.POST.get('etudiant'))
        compte, cree = models.CantineCompte.objects.get_or_create(etudiant=etudiant)
        if cree:
            messages.success(request, f'Compte cantine {compte.code_carte} créé pour {etudiant.nom_complet}.')
        else:
            messages.info(request, 'Ce compte cantine existait déjà.')
        return redirect('universite_comptes')
    etudiants = models.Etudiant.objects.filter(statut='actif') \
        .exclude(cantine__isnull=False)
    return render(request, 'universite/cantine/compte_create.html', {'etudiants': etudiants})


@personnel_uniquement
def compte_detail(request, pk):
    compte = get_object_or_404(models.CantineCompte.objects.select_related('etudiant'), pk=pk)
    recharges = compte.recharges.order_by('-date')
    commandes = compte.commandes.select_related('plat').order_by('-date')
    total_depense = commandes.filter(annule=False).aggregate(s=Sum('montant'))['s'] or 0
    total_recharge = recharges.aggregate(s=Sum('montant'))['s'] or 0
    return render(request, 'universite/cantine/compte_detail.html', {
        'compte': compte, 'recharges': recharges, 'commandes': commandes,
        'total_depense': total_depense, 'total_recharge': total_recharge})


@personnel_uniquement
def recharges(request):
    lignes = []
    for r in models.RechargeCantine.objects.select_related('compte__etudiant').order_by('-date')[:150]:
        lignes.append([
            r.date.strftime('%d/%m/%Y %H:%M'),
            c(f'{r.compte.etudiant.nom} {r.compte.etudiant.prenom}', url=reverse('universite_compte_detail', args=[r.compte.pk])),
            f'+{r.montant:,.0f}',
            r.mode,
            r.enregistre_par.username if r.enregistre_par else '—',
            c('Supprimer', url=reverse('universite_recharge_delete', args=[r.pk])),
        ])
    contexte = _contexte_liste(
        'Recharges de comptes', 'bi-cash-stack', ['Date', 'Étudiant', 'Montant', 'Mode', 'Par', 'Actions'],
        lignes, bouton='Nouvelle recharge', bouton_url=reverse('universite_recharge_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def recharge_delete(request, pk):
    recharge = get_object_or_404(models.RechargeCantine, pk=pk)
    if request.method == 'POST':
        recharge.compte.solde -= recharge.montant
        recharge.compte.save(update_fields=['solde'])
        recharge.delete()
        messages.success(request, 'Recharge supprimée, solde ajusté.')
        return redirect('universite_recharges')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(recharge), 'retour': reverse('universite_recharges')})


@personnel_uniquement
def recharge_create(request):
    form = RechargeCantineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        recharge = form.save(commit=False)
        recharge.enregistre_par = request.user
        recharge.save()
        recharge.compte.solde += recharge.montant
        recharge.compte.save(update_fields=['solde'])
        messages.success(request, f'Compte rechargé de {recharge.montant}.')
        return redirect('universite_recharges')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Recharger un compte', 'icone': 'bi-cash-stack',
        'form': form, 'retour': reverse('universite_recharges')})


@personnel_uniquement
def commandes_cantine(request):
    jour = request.GET.get('jour', '')
    qs = models.CommandeCantine.objects.select_related('compte__etudiant', 'plat').order_by('-date')
    if jour:
        qs = qs.filter(date__date=jour)
    lignes = []
    total = 0
    for cm in qs[:200]:
        total += 0 if cm.annule else cm.montant
        lignes.append([
            cm.date.strftime('%d/%m/%Y %H:%M'),
            c(f'{cm.compte.etudiant.nom} {cm.compte.etudiant.prenom}', url=reverse('universite_compte_detail', args=[cm.compte.pk])),
            cm.plat.nom,
            f'{cm.montant:,.0f}',
            _badge('actif' if not cm.annule else 'inactif'),
            c('Annuler', url=reverse('universite_commande_annuler', args=[cm.pk])) if not cm.annule else '—',
        ])
    contexte = _contexte_liste(
        'Commandes cantine', 'bi-receipt-cutoff', ['Date', 'Étudiant', 'Plat', 'Montant', 'État', 'Actions'],
        lignes, bouton='Nouvelle commande', bouton_url=reverse('universite_commande_create'))
    contexte['total'] = f'{total:,.0f}'
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def commande_create(request):
    form = CommandeCantineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        commande = form.save(commit=False)
        commande.montant = commande.plat.prix
        if commande.compte.solde < commande.montant:
            messages.error(request, 'Solde insuffisant sur le compte cantine.')
            return render(request, 'universite/partials/form.html', {
                'titre': 'Nouvelle commande', 'icone': 'bi-receipt-cutoff',
                'form': form, 'retour': reverse('universite_commandes')})
        commande.save()
        commande.compte.solde -= commande.montant
        commande.compte.save(update_fields=['solde'])
        messages.success(request, f'Commande {commande.plat.nom} servie.')
        return redirect('universite_commandes')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvelle commande', 'icone': 'bi-receipt-cutoff',
        'form': form, 'retour': reverse('universite_commandes')})


@personnel_uniquement
def commande_annuler(request, pk):
    commande = get_object_or_404(models.CommandeCantine, pk=pk)
    if request.method == 'POST' and not commande.annule:
        commande.compte.solde += commande.montant
        commande.compte.save(update_fields=['solde'])
        commande.annule = True
        commande.save(update_fields=['annule'])
        messages.success(request, 'Commande annulée, solde remboursé.')
    return redirect('universite_commandes')


@personnel_uniquement
def cantine_service(request):
    """Poste de service : recherche rapide d'un étudiant, recharge et service du repas."""
    aujourdhui = timezone.now().date()
    menus = list(models.MenuJour.objects.filter(date=aujourdhui).select_related('plat'))
    q = request.GET.get('q', '').strip()
    compte = None
    operations = []
    menus_deja_pris = set()
    if q:
        compte = models.CantineCompte.objects.select_related('etudiant').filter(
            Q(etudiant__matricule__icontains=q) | Q(etudiant__nom__icontains=q) |
            Q(etudiant__prenom__icontains=q) | Q(code_carte__icontains=q)).first()
    if request.method == 'POST':
        cpt = get_object_or_404(
            models.CantineCompte.objects.select_related('etudiant'),
            pk=request.POST.get('compte'))
        action = request.POST.get('action')
        if action == 'recharger':
            try:
                montant = Decimal(str(request.POST.get('montant', '0')).replace(',', '.').replace(' ', ''))
            except Exception:
                montant = Decimal('0')
            if montant <= 0:
                messages.error(request, 'Montant de recharge invalide.')
            else:
                with transaction.atomic():
                    models.RechargeCantine.objects.create(
                        compte=cpt, montant=montant,
                        mode=request.POST.get('mode', 'Especes'),
                        reference=request.POST.get('reference', ''),
                        enregistre_par=request.user)
                    cpt.solde += montant
                    cpt.save(update_fields=['solde'])
                messages.success(request, f'Compte de {cpt.etudiant.nom_complet} rechargé de {montant:,.0f} F. Nouveau solde : {cpt.solde:,.0f} F.')
        elif action == 'servir':
            menu = models.MenuJour.objects.select_related('plat').filter(
                pk=request.POST.get('menu'), date=aujourdhui).first()
            if not menu:
                messages.error(request, "Ce menu n'est pas programmé aujourd'hui.")
            elif not cpt.actif:
                messages.error(request, 'Ce compte cantine est désactivé.')
            elif cpt.solde < menu.plat.prix:
                messages.error(request, f"Solde insuffisant ({cpt.solde:,.0f} F) pour « {menu.plat.nom} » à {menu.plat.prix:,.0f} F. Rechargez le compte.")
            else:
                deja = models.CommandeCantine.objects.filter(compte=cpt, menu=menu, annule=False).exists()
                if deja and request.POST.get('forcer') != '1':
                    messages.warning(request, f"{cpt.etudiant.nom_complet} a déjà été servi(e) pour ce repas. Cochez « Autoriser le double service » pour forcer.")
                else:
                    with transaction.atomic():
                        models.CommandeCantine.objects.create(
                            compte=cpt, plat=menu.plat, menu=menu, montant=menu.plat.prix)
                        cpt.solde -= menu.plat.prix
                        cpt.save(update_fields=['solde'])
                    messages.success(request, f"Repas servi à {cpt.etudiant.nom_complet} : {menu.get_type_display()} — {menu.plat.nom}. Nouveau solde : {cpt.solde:,.0f} F.")
        return redirect(f"{reverse('universite_cantine_service')}?q={cpt.etudiant.matricule}")
    if compte:
        commandes_jour = models.CommandeCantine.objects.filter(
            compte=compte, annule=False, date__date=aujourdhui)
        menus_deja_pris = set(commandes_jour.values_list('menu_id', flat=True))
        operations = sorted(
            list(compte.recharges.all()[:8])
            + list(commandes_jour.select_related('plat')[:8]),
            key=lambda o: o.date, reverse=True)
    return render(request, 'universite/cantine/service.html', {
        'q': q, 'compte': compte, 'menus': menus, 'operations': operations,
        'menus_deja_pris': menus_deja_pris, 'aujourdhui': aujourdhui})


# ---------------------------------------------------------------------------
# Laboratoire virtuel interactif
# ---------------------------------------------------------------------------

@labo_uniquement
def labo(request):
    discipline = request.GET.get('discipline', '')
    niveau = request.GET.get('niveau', '')
    qs = models.ExperienceLabo.objects.filter(actif=True)
    if discipline:
        qs = qs.filter(discipline=discipline)
    if niveau:
        qs = qs.filter(niveau=niveau)
    exp = qs.order_by('discipline', 'niveau', 'titre')
    nb_par_discipline = {
        d[0]: models.ExperienceLabo.objects.filter(actif=True, discipline=d[0]).count()
        for d in models.ExperienceLabo.DISCIPLINES
    }
    nb_par_niveau = {
        n[0]: models.ExperienceLabo.objects.filter(actif=True, niveau=n[0]).count()
        for n in models.ExperienceLabo.NIVEAUX
    }
    mes_rapports = models.RapportExperience.objects.filter(etudiant__user=request.user).count() if hasattr(request.user, 'etudiant') else 0
    return render(request, 'universite/labo/accueil.html', {
        'experiences': exp, 'discipline': discipline, 'niveau': niveau,
        'disciplines': models.ExperienceLabo.DISCIPLINES,
        'niveaux': models.ExperienceLabo.NIVEAUX,
        'nb_par_discipline': nb_par_discipline,
        'nb_par_niveau': nb_par_niveau, 'mes_rapports': mes_rapports})


@labo_uniquement
def labo_experience(request, slug):
    experience = get_object_or_404(models.ExperienceLabo, slug=slug, actif=True)
    # Association automatique : étudiant connecté
    etudiant = None
    if hasattr(request.user, 'etudiant'):
        etudiant = request.user.etudiant
    if request.method == 'POST':
        parametres = request.POST.get('parametres', '')
        donnees = request.POST.get('donnees', '')
        analyse = request.POST.get('analyse', '')
        resultats = request.POST.get('resultats', '')
        observations = request.POST.get('observations', '')
        conclusion = request.POST.get('conclusion', '')
        if etudiant:
            rapport = models.RapportExperience.objects.create(
                etudiant=etudiant, experience=experience,
                parametres=parametres, donnees=donnees, analyse=analyse,
                resultats=resultats, observations=observations,
                conclusion=conclusion)
            messages.success(request, 'Rapport d\'expérience enregistré.')
            return redirect('universite_labo_rapports')
        messages.warning(request, 'Connectez-vous avec un compte étudiant pour sauvegarder.')
    return render(request, 'universite/labo/experience.html', {
        'experience': experience, 'etudiant': etudiant})


@labo_uniquement
def labo_rapports(request):
    if hasattr(request.user, 'etudiant'):
        rapports = request.user.etudiant.rapports_labo.select_related('experience').order_by('-date')
    else:
        rapports = models.RapportExperience.objects.select_related('etudiant', 'experience').order_by('-date')[:100]
    return render(request, 'universite/labo/rapports.html', {'rapports': rapports})


@labo_uniquement
def labo_rapport_csv(request, pk):
    rapport = get_object_or_404(models.RapportExperience, pk=pk)
    from django.http import HttpResponse
    if hasattr(request.user, 'etudiant'):
        if request.user.etudiant.id != rapport.etudiant.id:
            return redirect('universite_labo_rapports')
    csv = rapport.donnees or ''
    header = (f'# Rapport {rapport.experience.titre}\n'
              f'# Étudiant: {rapport.etudiant}\n'
              f'# Date: {rapport.date.strftime("%d/%m/%Y %H:%M")}\n'
              f'# Paramètres: {rapport.parametres.replace(chr(10), " | ")}\n'
              f'# Analyse: {rapport.analyse.replace(chr(10), " | ")}\n'
              f'# Résultats: {rapport.resultats.replace(chr(10), " | ")}\n'
              f'# Conclusion: {rapport.conclusion.replace(chr(10), " | ")}\n\n')
    filename = f'rapport_{rapport.experience.slug}_{rapport.id}.csv'
    response = HttpResponse(header + csv, content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@labo_uniquement
def labo_references(request):
    return render(request, 'universite/labo/references.html', {
        'pictogrammes': models.ExperienceLabo.PICTOGRAMMES,
        'disciplines': models.ExperienceLabo.DISCIPLINES,
    })


# ---------------------------------------------------------------------------
# Bibliothèque universitaire
# ---------------------------------------------------------------------------

@consultation_uniquement
def bibliotheque(request):
    lecture_seule = not est_personnel(request.user)
    lignes = []
    for o in models.Bibliographie.objects.all():
        lignes.append([
            o.titre,
            o.auteur or '—',
            o.get_domaine_display(),
            o.emplacement or '—',
            c(f'{o.disponibles} / {o.quantite}', badge='success' if o.disponibles else 'danger'),
            o.prets_en_cours,
        ])
    contexte = _contexte_liste(
        'Bibliothèque universitaire', 'bi-book', ['Ouvrage', 'Auteur', 'Domaine', 'Rayon', 'Disponibles', 'Prêts'],
        lignes,
        bouton=None if lecture_seule else 'Nouvel ouvrage',
        bouton_url=reverse('universite_livre_create'))
    contexte['lecture_seule'] = lecture_seule
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def livre_create(request):
    form = BibliographieForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Ouvrage ajouté.')
        return redirect('universite_bibliotheque')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouvel ouvrage', 'icone': 'bi-book',
        'form': form, 'retour': reverse('universite_bibliotheque')})


@personnel_uniquement
def prets(request):
    lignes = []
    for p in models.PretOuvrage.objects.select_related('ouvrage', 'etudiant').order_by('-date_pret'):
        lignes.append([
            p.ouvrage.titre,
            c(f'{p.etudiant.nom} {p.etudiant.prenom}', url=reverse('universite_etudiant_detail', args=[p.etudiant.pk])),
            p.date_pret.strftime('%d/%m/%Y'),
            p.date_retour_prevue.strftime('%d/%m/%Y'),
            _badge('retard' if p.en_retard else p.statut),
            c('Retour', url=reverse('universite_pret_retour', args=[p.pk])) if p.statut == 'en_cours' else '—',
        ])
    contexte = _contexte_liste(
        'Prêts d\'ouvrages', 'bi-journal-arrow-up', ['Ouvrage', 'Étudiant', 'Prêt', 'Retour prévu', 'État', 'Actions'],
        lignes, bouton='Nouveau prêt', bouton_url=reverse('universite_pret_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@personnel_uniquement
def pret_create(request):
    form = PretOuvrageForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        pret = form.save(commit=False)
        if pret.ouvrage.disponibles <= 0:
            messages.error(request, 'Aucun exemplaire disponible.')
            return render(request, 'universite/partials/form.html', {
                'titre': 'Nouveau prêt', 'icone': 'bi-journal-arrow-up',
                'form': form, 'retour': reverse('universite_prets')})
        pret.save()
        messages.success(request, 'Prêt enregistré.')
        return redirect('universite_prets')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Nouveau prêt', 'icone': 'bi-journal-arrow-up',
        'form': form, 'retour': reverse('universite_prets')})


@personnel_uniquement
def pret_retour(request, pk):
    pret = get_object_or_404(models.PretOuvrage, pk=pk)
    if request.method == 'POST':
        pret.statut = 'rendu'
        pret.date_retour_reel = timezone.now().date()
        pret.save(update_fields=['statut', 'date_retour_reel'])
        messages.success(request, 'Ouvrage retourné.')
    return redirect('universite_prets')


# ---------------------------------------------------------------------------
# Rapports & configuration
# ---------------------------------------------------------------------------

@personnel_uniquement
def rapports(request):
    annee = models.AnneeAcademique.en_cours()
    par_faculte = []
    for f in models.Faculte.objects.all():
        effectif = models.Inscription.objects.filter(annee=annee, filiere__departement__faculte=f,
                                                     statut='active').count()
        par_faculte.append({'faculte': f, 'effectif': effectif})
    total_etudiants = sum(x['effectif'] for x in par_faculte)
    par_filiere = models.Inscription.objects.filter(annee=annee, statut='active') \
        .values('filiere__nom').annotate(n=Count('id')).order_by('-n')
    total_paye = models.Paiement.objects.filter(annee=annee).aggregate(s=Sum('montant'))['s'] or 0
    total_cantine = models.CommandeCantine.objects.filter(annule=False).aggregate(s=Sum('montant'))['s'] or 0
    prets_retard = models.PretOuvrage.objects.filter(statut='en_cours') \
        .filter(date_retour_prevue__lt=timezone.now().date()).count()
    absences = models.Presence.objects.filter(statut='Absent').count()
    return render(request, 'universite/rapport/rapports.html', {
        'annee': annee, 'par_faculte': par_faculte, 'total_etudiants': total_etudiants,
        'par_filiere': par_filiere, 'total_paye': total_paye, 'total_cantine': total_cantine,
        'prets_retard': prets_retard, 'absences': absences})


@superuser_uniquement
def parametres(request):
    objet = models.UniversiteParametre.obtenir()
    form = UniversiteParametreForm(request.POST or None, request.FILES or None, instance=objet)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Paramètres mis à jour.')
        return redirect('universite_parametres')
    return render(request, 'universite/partials/form.html', {
        'titre': 'Paramètres de l\'université', 'icone': 'bi-gear',
        'form': form, 'retour': reverse('universite_dashboard')})


@superuser_uniquement
def utilisateurs(request):
    Utilisateur = get_user_model()
    lignes = []
    for u in Utilisateur.objects.all().order_by('username'):
        groupes = ', '.join(u.groups.values_list('name', flat=True)) or '—'
        nb_pages = u.pages_visibles.count()
        pages_cell = f'{nb_pages} page(s)' if nb_pages else 'Toutes'
        actions = [
            c('Modifier', url=reverse('universite_utilisateur_update', args=[u.pk])),
            c('Désactiver' if u.is_active else 'Activer',
              url=reverse('universite_utilisateur_activer', args=[u.pk])),
            c('Supprimer', url=reverse('universite_utilisateur_delete', args=[u.pk])),
        ]
        lignes.append([
            u.username,
            u.get_full_name() or '—',
            c(u.email, url=f'mailto:{u.email}') if u.email else '—',
            groupes,
            _badge('actif' if u.is_active else 'inactif'),
            c('Superadmin' if u.is_superuser else 'Standard',
              badge='dark' if u.is_superuser else 'info'),
            pages_cell,
            *actions,
        ])
    contexte = _contexte_liste(
        'Utilisateurs & rôles', 'bi-person-gear',
        ['Identifiant', 'Nom complet', 'Email', 'Groupes', 'Statut', 'Droits', 'Pages', '', '', ''],
        lignes, bouton='Nouvel utilisateur', bouton_url=reverse('universite_utilisateur_create'))
    return render(request, 'universite/partials/liste.html', contexte)


@superuser_uniquement
def utilisateur_create(request):
    synchroniser_pages()
    Utilisateur = get_user_model()
    pages = models.Page.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        nom = request.POST.get('nom', '')
        email = request.POST.get('email', '')
        mot_de_passe = request.POST.get('mot_de_passe', '')
        est_admin = request.POST.get('est_admin') == 'on'
        codes_selectionnes = set(request.POST.getlist('pages'))
        if not username or not mot_de_passe:
            messages.error(request, 'Identifiant et mot de passe obligatoires.')
        elif Utilisateur.objects.filter(username=username).exists():
            messages.error(request, 'Cet identifiant existe déjà.')
        else:
            utilisateur = Utilisateur.objects.create_user(
                username=username, email=email, first_name=nom, password=mot_de_passe,
                is_staff=est_admin, is_superuser=False)
            utilisateur.groups.add(Group.objects.get_or_create(name='Gestionnaire universitaire')[0])
            if codes_selectionnes:
                utilisateur.pages_visibles.set(
                    models.Page.objects.filter(code__in=codes_selectionnes))
            messages.success(request, f'Utilisateur {username} créé.')
            return redirect('universite_utilisateurs')
    pages_groupes = _pages_groupes(pages)
    return render(request, 'universite/utilisateur/form.html', {
        'retour': reverse('universite_utilisateurs'), 'pages': pages,
        'pages_groupes': pages_groupes, 'mode': 'create',
        'titre': 'Nouvel utilisateur'})


@superuser_uniquement
def utilisateur_update(request, pk):
    synchroniser_pages()
    Utilisateur = get_user_model()
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    pages = models.Page.objects.all()
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        if not username:
            messages.error(request, 'L\'identifiant est obligatoire.')
            return redirect('universite_utilisateur_update', pk=pk)
        utilisateur.username = username
        utilisateur.first_name = request.POST.get('nom', '')
        utilisateur.email = request.POST.get('email', '')
        mot_de_passe = request.POST.get('mot_de_passe', '')
        if mot_de_passe:
            utilisateur.set_password(mot_de_passe)
        if not utilisateur.is_superuser:
            utilisateur.is_staff = request.POST.get('est_admin') == 'on'
            codes_selectionnes = set(request.POST.getlist('pages'))
            utilisateur.pages_visibles.set(
                models.Page.objects.filter(code__in=codes_selectionnes))
        utilisateur.save()
        messages.success(request, f'Utilisateur {utilisateur.username} mis à jour.')
        return redirect('universite_utilisateurs')
    pages_groupes = _pages_groupes(pages)
    codes_actuels = set(utilisateur.pages_visibles.values_list('code', flat=True))
    return render(request, 'universite/utilisateur/form.html', {
        'retour': reverse('universite_utilisateurs'), 'pages': pages,
        'pages_groupes': pages_groupes, 'utilisateur': utilisateur,
        'codes_actuels': codes_actuels, 'mode': 'edit',
        'titre': f'Modifier {utilisateur.username}'})


@superuser_uniquement
def utilisateur_activer(request, pk):
    Utilisateur = get_user_model()
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if utilisateur.is_superuser:
        messages.error(request, 'Impossible de désactiver un superadministrateur.')
    elif utilisateur.pk == request.user.pk:
        messages.error(request, 'Impossible de désactiver votre propre compte.')
    else:
        utilisateur.is_active = not utilisateur.is_active
        utilisateur.save()
        messages.success(
            request,
            f'{utilisateur.username} {"réactivé" if utilisateur.is_active else "désactivé"}.')
    return redirect('universite_utilisateurs')


@superuser_uniquement
def utilisateur_delete(request, pk):
    Utilisateur = get_user_model()
    utilisateur = get_object_or_404(Utilisateur, pk=pk)
    if utilisateur.is_superuser or utilisateur.pk == request.user.pk:
        messages.error(request, 'Impossible de supprimer ce compte.')
        return redirect('universite_utilisateurs')
    if request.method == 'POST':
        nom = utilisateur.username
        utilisateur.delete()
        messages.success(request, f'Utilisateur {nom} supprimé.')
        return redirect('universite_utilisateurs')
    return render(request, 'universite/confirmer_suppression.html', {
        'objet': str(utilisateur), 'retour': reverse('universite_utilisateurs')})


# ---------------------------------------------------------------------------
# Inscription libre d'un étudiant (auto-création de compte)
# ---------------------------------------------------------------------------

def inscription_etudiant(request):
    """Permet à un étudiant de créer son propre compte depuis son matricule."""
    if request.user.is_authenticated:
        return redirect('universite_dashboard')
    Utilisateur = get_user_model()

    def _erreur(msg, valeurs):
        messages.error(request, msg)
        return render(request, 'universite/auth/inscription.html', {'valeurs': valeurs})

    if request.method == 'POST':
        valeurs = {
            'matricule': request.POST.get('matricule', '').strip(),
            'nom': request.POST.get('nom', '').strip(),
            'prenom': request.POST.get('prenom', '').strip(),
            'username': request.POST.get('username', '').strip(),
            'email': request.POST.get('email', '').strip(),
        }
        mot_de_passe = request.POST.get('mot_de_passe', '')
        confirmation = request.POST.get('confirmation', '')

        if not (valeurs['matricule'] and valeurs['nom'] and valeurs['prenom']
                and valeurs['username'] and mot_de_passe):
            return _erreur('Tous les champs obligatoires doivent être remplis.', valeurs)
        if mot_de_passe != confirmation:
            return _erreur('Les deux mots de passe ne correspondent pas.', valeurs)

        etudiant = models.Etudiant.objects.filter(matricule__iexact=valeurs['matricule']).first()
        if not etudiant:
            return _erreur('Aucun étudiant ne correspond à ce matricule.', valeurs)
        if (valeurs['nom'].lower(), valeurs['prenom'].lower()) != (
                etudiant.nom.strip().lower(), etudiant.prenom.strip().lower()):
            return _erreur('Le nom ou le prénom ne correspondent pas à ce matricule.', valeurs)
        if etudiant.user is not None:
            return _erreur(
                'Un compte existe déjà pour cet étudiant. Utilisez la page de connexion.', valeurs)
        if Utilisateur.objects.filter(username__iexact=valeurs['username']).exists():
            return _erreur('Ce nom d\'utilisateur est déjà pris.', valeurs)
        if valeurs['email'] and Utilisateur.objects.filter(email__iexact=valeurs['email']).exists():
            return _erreur('Cette adresse email est déjà utilisée.', valeurs)

        utilisateur = Utilisateur(
            username=valeurs['username'], email=valeurs['email'],
            first_name=etudiant.prenom, last_name=etudiant.nom)
        try:
            validate_password(mot_de_passe, utilisateur)
        except ValidationError as e:
            return _erreur('; '.join(e.messages), valeurs)

        utilisateur.set_password(mot_de_passe)
        utilisateur.save()
        etudiant.user = utilisateur
        etudiant.save(update_fields=['user'])
        auth_login(request, utilisateur)
        messages.success(
            request, f'Bienvenue {etudiant.prenom} ! Votre compte a été créé avec succès.')
        return redirect('universite_dashboard')

    return render(request, 'universite/auth/inscription.html', {'valeurs': {}})


# ---------------------------------------------------------------------------
# Sauvegardes & restauration
# ---------------------------------------------------------------------------

@superuser_uniquement
def sauvegarde(request):
    """Page de gestion des sauvegardes : liste, création, téléchargement."""
    return render(request, 'universite/sauvegarde/sauvegarde.html', {
        'sauvegardes': lister_sauvegardes(),
        'dossier_sauvegardes': dossier_sauvegardes(),
    })


@superuser_uniquement
def sauvegarde_creer(request):
    if request.method == 'POST':
        try:
            s = creer_sauvegarde(
                automatique=False, max_conservation=settings.SAUVEGARDE_RETENTION)
            messages.success(request, f'Sauvegarde créée : {s.fichier}')
        except Exception as e:
            messages.error(request, f'Échec de la sauvegarde : {e}')
    return redirect('universite_sauvegarde')


@superuser_uniquement
def sauvegarde_telecharger(request, pk):
    s = get_object_or_404(models.Sauvegarde, pk=pk)
    chemin = dossier_sauvegardes() / Path(s.fichier).name
    if not chemin.exists():
        messages.error(request, 'Fichier de sauvegarde introuvable.')
        return redirect('universite_sauvegarde')
    return FileResponse(chemin.open('rb'), as_attachment=True, filename=chemin.name)


@superuser_uniquement
def sauvegarde_restaurer(request, pk):
    s = get_object_or_404(models.Sauvegarde, pk=pk)
    chemin = dossier_sauvegardes() / Path(s.fichier).name
    if not chemin.exists():
        messages.error(request, 'Fichier de sauvegarde introuvable.')
        return redirect('universite_sauvegarde')
    if request.method == 'POST':
        try:
            resultat = restaurer_sauvegarde(s)
            messages.success(
                request,
                f'Restauration effectuée depuis {resultat["fichier"]} '
                f'(médias : {"oui" if resultat["medias"] else "non"}). '
                'Veuillez vous reconnecter.')
        except Exception as e:
            messages.error(request, f'Échec de la restauration : {e}')
        return redirect('universite_sauvegarde')
    return render(request, 'universite/sauvegarde/restaurer.html', {
        'sauvegarde': s, 'retour': reverse('universite_sauvegarde')})


@superuser_uniquement
def sauvegarde_supprimer(request, pk):
    s = get_object_or_404(models.Sauvegarde, pk=pk)
    if request.method == 'POST':
        chemin = dossier_sauvegardes() / Path(s.fichier).name
        if chemin.exists():
            chemin.unlink()
        s.delete()
        messages.success(request, f'Sauvegarde {s.fichier} supprimée.')
    return redirect('universite_sauvegarde')





