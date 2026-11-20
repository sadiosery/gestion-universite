"""Sauvegardes exploitables pour UniversiteGest.

Chaque sauvegarde est un fichier ``.zip`` autonome contenant :
  - ``db.sqlite3``      : copie binaire de la base (restaurable telle quelle) ;
  - ``dumpdata.json``   : export JSON portable de toutes les données (``loaddata``) ;
  - ``media/``          : fichiers téléversés (photos, logos…) ;
  - ``metadonnees.txt`` : horodatage, version Django et contenu.

Utilisé par la page « Sauvegardes », la commande ``sauvegarde_bd`` et le
déclencheur automatique à la connexion.
"""
import io
import shutil
import sqlite3
import sys
import tempfile
import zipfile
from datetime import datetime, timedelta
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.utils import timezone

from .models import Sauvegarde


def _tests_en_cours():
    return 'test' in sys.argv


def chemin_base():
    """Chemin absolu du fichier SQLite principal."""
    return Path(settings.DATABASES['default']['NAME'])


def dossier_sauvegardes():
    """Dossier des sauvegardes (défaut : ``SAUVEGARDE_DOSSIER``)."""
    dossier = Path(getattr(settings, 'SAUVEGARDE_DOSSIER', 'sauvegardes'))
    if not dossier.is_absolute():
        dossier = chemin_base().parent / dossier
    dossier.mkdir(parents=True, exist_ok=True)
    return dossier


def dossier_medias():
    return Path(settings.MEDIA_ROOT)


def _dumpdata_json():
    """Retourne le JSON portable de toutes les données (bytes UTF-8)."""
    buffer = io.StringIO()
    call_command('dumpdata', exclude=['contenttypes', 'sessions', 'admin.logentry'],
                 stdout=buffer, format='json', indent=2)
    return buffer.getvalue().encode('utf-8')


def creer_sauvegarde(automatique=False, max_conservation=None):
    """Crée une sauvegarde zip autonome (base + dump JSON + médias).

    Retourne l'instance ``Sauvegarde`` créée, ou lève ``OSError`` si la base
    n'est pas accessible. Applique la rétention si ``max_conservation`` donné.
    """
    base = chemin_base()
    if not base.exists():
        raise OSError(f'Base de données introuvable : {base}')

    horodatage = datetime.now().strftime('%Y%m%d_%H%M%S')
    dossier = dossier_sauvegardes()
    nom = f'sauvegarde_universite_{horodatage}.zip'
    compteur = 1
    while (dossier / nom).exists():
        nom = f'sauvegarde_universite_{horodatage}_{compteur}.zip'
        compteur += 1
    cible = dossier / nom

    dump = _dumpdata_json()
    media_root = dossier_medias()

    metadonnees = (
        f'Sauvegarde UniversiteGest\n'
        f'Date : {datetime.now().strftime("%d/%m/%Y %H:%M:%S")}\n'
        f'Contenu : db.sqlite3, dumpdata.json, media/\n'
        f'Automatique : {"oui" if automatique else "non"}\n'
    ).encode('utf-8')

    with zipfile.ZipFile(cible, 'w', zipfile.ZIP_DEFLATED) as z:
        z.write(base, arcname='db.sqlite3')
        z.writestr('dumpdata.json', dump)
        z.writestr('metadonnees.txt', metadonnees)
        if media_root.exists():
            for fichier in media_root.rglob('*'):
                if fichier.is_file():
                    z.write(fichier, arcname=str(fichier.relative_to(media_root.parent)))

    sauvegarde = Sauvegarde.objects.create(
        fichier=nom, taille_octets=cible.stat().st_size, automatique=automatique)
    if max_conservation:
        purge_sauvegardes(max_conservation)
    return sauvegarde


def lister_sauvegardes():
    """Liste des dicts décrivant les sauvegardes (fichiers + traces)."""
    dossier = dossier_sauvegardes()
    resultats = []
    for s in Sauvegarde.objects.all():
        chemin = dossier / Path(s.fichier).name
        if not chemin.exists():
            continue
        resultats.append({
            'id': s.id, 'fichier': chemin.name, 'taille': s.taille_octets,
            'automatique': s.automatique, 'date': s.date,
        })
    for chemin in sorted(dossier.glob('sauvegarde_universite_*.zip'), reverse=True):
        if not Sauvegarde.objects.filter(fichier__endswith=chemin.name).exists():
            resultats.append({
                'fichier': chemin.name, 'taille': chemin.stat().st_size,
                'automatique': False, 'date': None,
            })
    return sorted(resultats, key=lambda s: s.get('date') or timezone.now(),
                  reverse=True)


def purge_sauvegardes(max_conservation):
    """Supprime les sauvegardes au-delà de ``max_conservation`` (fichiers + traces)."""
    if max_conservation <= 0:
        return 0
    dossier = dossier_sauvegardes()
    ordonnees = Sauvegarde.objects.all().order_by('-date')
    supprimees = 0
    for s in ordonnees[max_conservation:]:
        chemin = dossier / Path(s.fichier).name
        if chemin.exists():
            chemin.unlink()
        s.delete()
        supprimees += 1
    return supprimees


def sauvegarde_si_requise():
    """Crée une sauvegarde automatique si la dernière date de plus de
    ``SAUVEGARDE_INTERVALLE_HEURES`` heures (ou si aucune n'existe).

    Retourne ``(cree, sauvegarde)``. Jamais bloquant : toute erreur est
    absorbée pour ne pas interrompre le flux utilisateur.
    """
    if not getattr(settings, 'SAUVEGARDE_AUTO', True) or _tests_en_cours():
        return False, None
    try:
        intervalle = timedelta(hours=settings.SAUVEGARDE_INTERVALLE_HEURES)
        derniere = Sauvegarde.objects.order_by('-date').first()
        if derniere and timezone.now() - derniere.date < intervalle:
            return False, derniere
        s = creer_sauvegarde(automatique=True,
                             max_conservation=settings.SAUVEGARDE_RETENTION)
        return True, s
    except Exception:
        return False, None


def _valider_base_sqlite(chemin):
    """Vérifie que le fichier est bien une base SQLite lisible."""
    if not chemin.exists() or chemin.stat().st_size == 0:
        raise OSError('Fichier de base vide ou absent dans l\'archive.')
    connexion = sqlite3.connect(str(chemin))
    try:
        connexion.execute('SELECT count(*) FROM sqlite_master')
        connexion.commit()
    finally:
        connexion.close()
    return chemin


def restaurer_sauvegarde(sauvegarde):
    """Remplace la base actuelle par celle de la sauvegarde et restaure les médias.

    La base SQLite de l'archive est d'abord copiée dans un répertoire
    temporaire et validée, puis échangée atomiquement (``os.replace``) avec la
    base courante. Retourne un résumé descriptif.
    """
    from django.db import connections

    dossier = dossier_sauvegardes()
    archive = dossier / Path(sauvegarde.fichier).name
    if not archive.exists():
        raise OSError(f'Archive de sauvegarde introuvable : {archive.name}')

    base = chemin_base()
    medias_restaures = False

    with tempfile.TemporaryDirectory() as temp:
        temp_dir = Path(temp)
        with zipfile.ZipFile(archive) as z:
            if 'db.sqlite3' not in z.namelist():
                raise OSError('L\'archive ne contient pas de base SQLite (db.sqlite3).')
            z.extract('db.sqlite3', temp)
            if 'dumpdata.json' in z.namelist():
                z.extract('dumpdata.json', temp)
            noms_media = [n for n in z.namelist() if n.startswith('media/')]
            for nom in noms_media:
                z.extract(nom, temp)

        extrait = _valider_base_sqlite(temp_dir / 'db.sqlite3')

        connections.close_all()
        shutil.copy2(extrait, base)

        # Restauration des médias (fusion, écrasement)
        if (temp_dir / 'media').exists():
            media_root = dossier_medias()
            media_root.mkdir(parents=True, exist_ok=True)
            for source in (temp_dir / 'media').rglob('*'):
                if source.is_file():
                    cible = media_root / source.relative_to(temp_dir / 'media')
                    cible.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, cible)
            medias_restaures = True

    return {
        'fichier': sauvegarde.fichier,
        'base': base.name,
        'medias': medias_restaures,
    }
