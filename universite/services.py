from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from .models import (Etudiant, Note, UniteEnseignement, UniversiteParametre,
                     ValidationUE)


# ---------------------------------------------------------------------------
# Notes & moyennes
# ---------------------------------------------------------------------------

def moyenne_ue(etudiant, ue, session='Normale'):
    """Moyenne pondérée d'un étudiant sur une UE (session normale ou rattrapage)."""
    notes = Note.objects.filter(etudiant=etudiant, ue=ue)
    if session == 'Normale':
        notes = notes.exclude(type='RAT')
    else:
        notes = notes.filter(type='RAT')
    if not notes.exists():
        return None
    total_pondere = sum(Decimal(n.note) * Decimal(Note.POIDS[n.type]) for n in notes)
    poids_total = sum(Note.POIDS[n.type] for n in notes)
    return (total_pondere / poids_total).quantize(Decimal('0.01'))


def moyenne_etudiant(etudiant):
    """Moyenne générale (toutes UE confondues, notes normales)."""
    notes = Note.objects.filter(etudiant=etudiant).exclude(type='RAT')
    if not notes.exists():
        return Decimal('0.00')
    total = sum(Decimal(n.note) * Decimal(Note.POIDS[n.type]) for n in notes)
    poids = sum(Note.POIDS[n.type] for n in notes)
    return (total / poids).quantize(Decimal('0.01'))


# ---------------------------------------------------------------------------
# CGPA / crédits (système LMD)
# ---------------------------------------------------------------------------

def cgpa_etudiant(etudiant):
    """Moyenne pondérée par les crédits des UE acquises (système ECTS)."""
    validations = ValidationUE.objects.filter(etudiant=etudiant, decision__in=['valide', 'compense', 'credit'])
    if not validations.exists():
        return Decimal('0.00'), 0, 0
    total_notes = sum(v.moyenne * v.ue.credits for v in validations)
    total_credits = sum(v.ue.credits for v in validations)
    if total_credits == 0:
        return Decimal('0.00'), 0, 0
    return (total_notes / total_credits).quantize(Decimal('0.01')), total_credits, validations.count()


def credits_acquis(etudiant):
    return ValidationUE.objects.filter(etudiant=etudiant, decision__in=['valide', 'compense', 'credit']) \
        .aggregate(total=Sum('ue__credits'))['total'] or 0


# ---------------------------------------------------------------------------
# Décision de semestre (compensation LMD)
# ---------------------------------------------------------------------------

def decider_ues(etudiant, semestre):
    """Calcule et crée les validations d'UE pour un semestre (session normale)."""
    ues = UniteEnseignement.objects.filter(semestre=semestre, filiere=etudiant.filiere)
    resultats = []
    for ue in ues:
        moyenne = moyenne_ue(etudiant, ue)
        if moyenne is None:
            continue
        seuil = UniversiteParametre.obtenir().seuil_validation
        decision = 'valide' if moyenne >= seuil else 'echoue'
        validation, _ = ValidationUE.objects.update_or_create(
            etudiant=etudiant, ue=ue, semestre=semestre,
            defaults={'moyenne': moyenne, 'decision': decision, 'session': 'Normale'},
        )
        resultats.append(validation)
    return resultats


def moyenne_semestre(etudiant, semestre):
    ues = UniteEnseignement.objects.filter(semestre=semestre, filiere=etudiant.filiere)
    notes = Note.objects.filter(etudiant=etudiant, ue__in=ues).exclude(type='RAT')
    if not notes.exists():
        return None
    total = sum(Decimal(n.note) * Decimal(Note.POIDS[n.type]) for n in notes)
    poids = sum(Note.POIDS[n.type] for n in notes)
    return (total / poids).quantize(Decimal('0.01'))


# ---------------------------------------------------------------------------
# Montants en lettres (reçus)
# ---------------------------------------------------------------------------

_UNITES = ('', 'un', 'deux', 'trois', 'quatre', 'cinq', 'six', 'sept', 'huit', 'neuf',
           'dix', 'onze', 'douze', 'treize', 'quatorze', 'quinze', 'seize',
           'dix-sept', 'dix-huit', 'dix-neuf')


def _sous_centaine(n, suivi=False):
    n %= 100
    if n < 20:
        return _UNITES[n]
    dizaines = {20: 'vingt', 30: 'trente', 40: 'quarante', 50: 'cinquante', 60: 'soixante',
                70: 'soixante-dix', 80: 'quatre-vingt', 90: 'quatre-vingt-dix'}
    d = (n // 10) * 10
    u = n % 10
    if u == 0:
        if d == 80 and not suivi:
            return 'quatre-vingts'
        return dizaines[d]
    if d == 70:
        return f'soixante-{_UNITES[10 + u]}'
    if d == 90:
        return f'quatre-vingt-{_UNITES[10 + u]}'
    return f'{dizaines[d]}-{_UNITES[u]}'


def _trois_chiffres(n, suivi=False):
    n %= 1000
    centaines = n // 100
    reste = n % 100
    if centaines == 0:
        return _sous_centaine(reste, suivi=suivi)
    c = 'cent' if centaines == 1 else f'{_UNITES[centaines]} cent'
    if reste == 0 and centaines > 1 and not suivi:
        c += 's'
    if reste:
        return f'{c} {_sous_centaine(reste)}'
    return c


def montant_en_lettres(montant):
    montant = int(Decimal(montant))
    if montant == 0:
        return 'zéro'
    if montant < 0:
        return f'moins {montant_en_lettres(-montant)}'
    millions = montant // 1000000
    milliers = (montant // 1000) % 1000
    reste = montant % 1000
    parties = []
    if millions:
        parties.append('un million' if millions == 1 else f'{_trois_chiffres(millions, suivi=True)} millions')
    if milliers:
        parties.append('mille' if milliers == 1 else f'{_trois_chiffres(milliers, suivi=True)} mille')
    if reste:
        parties.append(_trois_chiffres(reste))
    return ' '.join(parties)


# ---------------------------------------------------------------------------
# Statistiques du tableau de bord
# ---------------------------------------------------------------------------

def stats_dashboard():
    from .models import (AnneeAcademique, Enseignant, Etudiant,
                         Faculte, Inscription, UniteEnseignement)
    annee = AnneeAcademique.en_cours()
    return {
        'etudiants': Etudiant.objects.count(),
        'actifs': Inscription.objects.filter(statut='active').count(),
        'enseignants': Enseignant.objects.count(),
        'ues': UniteEnseignement.objects.count(),
        'facultes': Faculte.objects.count(),
        'hommes': Etudiant.objects.filter(sexe='M').count(),
        'femmes': Etudiant.objects.filter(sexe='F').count(),
        'boursiers': Etudiant.objects.filter(boursier=True).count(),
        'annee': annee,
    }
