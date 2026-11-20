"""Commande de sauvegarde / restauration de la base UniversiteGest.

Usage :
    python manage.py sauvegarde_bd                     # crée une sauvegarde
    python manage.py sauvegarde_bd --liste             # liste les sauvegardes
    python manage.py sauvegarde_bd --restaurer <fichier.zip>
    python manage.py sauvegarde_bd --conserver 10      # rétention

Peut être planifiée (Planificateur de tâches Windows) pour des sauvegardes
automatiques régulières.
"""
from django.core.management.base import BaseCommand, CommandError

from universite.sauvegarde import (creer_sauvegarde, dossier_sauvegardes,
                                   lister_sauvegardes, purge_sauvegardes,
                                   restaurer_sauvegarde)
from universite.models import Sauvegarde


class Command(BaseCommand):
    help = 'Sauvegarde la base (copie SQLite + dump JSON + médias) dans un zip avec rotation.'

    def add_arguments(self, parser):
        parser.add_argument('--conserver', type=int, default=None,
                            help='Nombre de sauvegardes à conserver (défaut : SAUVEGARDE_RETENTION).')
        parser.add_argument('--liste', action='store_true', help='Liste les sauvegardes existantes.')
        parser.add_argument('--restaurer', metavar='FICHIER',
                            help='Nom du fichier .zip à restaurer (dans le dossier de sauvegardes).')

    def handle(self, *args, **options):
        from django.conf import settings
        retention = options['conserver'] or settings.SAUVEGARDE_RETENTION

        if options['restaurer']:
            fichier = options['restaurer']
            dossier = dossier_sauvegardes()
            archive = dossier / fichier
            if not archive.exists():
                raise CommandError(f'Archive introuvable dans {dossier} : {fichier}')
            s, _ = Sauvegarde.objects.get_or_create(
                fichier=fichier,
                defaults={'taille_octets': archive.stat().st_size})
            resultat = restaurer_sauvegarde(s)
            self.stdout.write(self.style.SUCCESS(
                f'Restauration effectuée depuis {resultat["fichier"]} '
                f'(base : {resultat["base"]}, médias : {"oui" if resultat["medias"] else "non"}).'))
            return

        if options['liste']:
            liste = lister_sauvegardes()
            if not liste:
                self.stdout.write('Aucune sauvegarde trouvée.')
                return
            for s in liste:
                date = s.get('date').strftime('%d/%m/%Y %H:%M') if s.get('date') else 'fichier orphelin'
                taille = f'{s["taille"] / 1024:.1f} Ko'
                type_s = 'auto' if s['automatique'] else 'manuel'
                self.stdout.write(f'  {s["fichier"]:<45} {date}  {taille:>10}  {type_s}')
            return

        sauvegarde = creer_sauvegarde(automatique=False, max_conservation=retention)
        self.stdout.write(self.style.SUCCESS(
            f'Sauvegarde créée : {sauvegarde.fichier} '
            f'({sauvegarde.taille_octets / 1024:.1f} Ko)'))
        purges = purge_sauvegardes(retention)
        if purges:
            self.stdout.write(f'{purges} sauvegarde(s) ancienne(s) supprimée(s).')
