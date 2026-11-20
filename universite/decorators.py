from functools import wraps

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

GROUPES_PERSONNEL = {'Gestionnaire universitaire', 'Administrateur'}


def est_personnel(user):
    """Vrai pour le superutilisateur ou les groupes du personnel universitaire."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    groupes = set(user.groups.values_list('name', flat=True))
    return bool(groupes & GROUPES_PERSONNEL)


def est_etudiant(user):
    """Vrai pour un utilisateur connecté possédant un profil étudiant."""
    return bool(user and user.is_authenticated and hasattr(user, 'etudiant'))


def roles_requis(*noms):
    """Interdit l'accès sauf superuser ou appartenance à l'un des groupes."""
    def decorateur(vue):
        @wraps(vue)
        def _wrapped(request, *args, **kwargs):
            if request.user.is_superuser:
                return vue(request, *args, **kwargs)
            groupes = set(request.user.groups.values_list('name', flat=True))
            if noms and not set(noms) & groupes:
                raise PermissionDenied
            return vue(request, *args, **kwargs)
        return _wrapped
    return decorateur


def personnel_uniquement(vue):
    """Réservé au personnel connecté (gestionnaire, administratif, admin).

    Les autres utilisateurs (étudiants…) sont redirigés vers le portail
    étudiant (laboratoire virtuel).
    """
    @wraps(vue)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if est_personnel(request.user):
            return vue(request, *args, **kwargs)
        messages.warning(request, 'Accès réservé au personnel de l\'université.')
        return redirect('universite_labo')
    return _wrapped


def labo_uniquement(vue):
    """Réservé au portail laboratoire : étudiants et personnel uniquement."""
    @wraps(vue)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if est_personnel(request.user) or est_etudiant(request.user):
            return vue(request, *args, **kwargs)
        messages.warning(request, 'Accès réservé aux étudiants et au personnel.')
        return redirect('login')
    return _wrapped


def consultation_uniquement(vue):
    """Lecture autorisée au personnel et aux étudiants connectés."""
    @wraps(vue)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if est_personnel(request.user) or est_etudiant(request.user):
            return vue(request, *args, **kwargs)
        messages.warning(request, 'Accès réservé aux utilisateurs connectés.')
        return redirect('login')
    return _wrapped


def superuser_uniquement(vue):
    """Réservé au superutilisateur."""
    @wraps(vue)
    def _wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.is_superuser:
            return vue(request, *args, **kwargs)
        messages.warning(request, 'Accès réservé à l\'administrateur.')
        return redirect('universite_dashboard')
    return _wrapped
