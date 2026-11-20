from .decorators import est_etudiant, est_personnel
from .models import AnneeAcademique, UniversiteParametre


def parametres_universite(request):
    pages = None
    if request.user.is_authenticated and not request.user.is_superuser:
        codes = set(request.user.pages_visibles.values_list('code', flat=True))
        pages = codes if codes else None
    return {
        'universite_parametres': UniversiteParametre.obtenir(),
        'annee_universitaire': AnneeAcademique.en_cours(),
        'est_personnel': bool(request.user.is_authenticated and est_personnel(request.user)),
        'est_etudiant': bool(request.user.is_authenticated and est_etudiant(request.user)),
        'pages_visibles': pages,
    }
