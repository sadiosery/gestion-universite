"""Ajoute la page « Sauvegardes » au catalogue de visibilité."""

from django.db import migrations

from universite.pages_catalogue import PAGES


def seed_sauvegarde(apps, schema_editor):
    Page = apps.get_model('universite', 'Page')
    code, titre, url, section, _urls = next(
        p for p in PAGES if p[0] == 'sauvegarde')
    Page.objects.get_or_create(code=code, defaults={
        'titre': titre, 'url_name': url, 'section': section})


def annuler(apps, schema_editor):
    Page = apps.get_model('universite', 'Page')
    Page.objects.filter(code='sauvegarde').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('universite', '0006_sauvegarde'),
    ]

    operations = [
        migrations.RunPython(seed_sauvegarde, annuler),
    ]
