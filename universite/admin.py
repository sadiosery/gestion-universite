from django.contrib import admin

from . import models


@admin.register(models.UniversiteParametre)
class UniversiteParametreAdmin(admin.ModelAdmin):
    list_display = ('nom_universite', 'recteur', 'email')


@admin.register(models.AnneeAcademique)
class AnneeAcademiqueAdmin(admin.ModelAdmin):
    list_display = ('libelle', 'date_debut', 'date_fin', 'active')


@admin.register(models.Semestre)
class SemestreAdmin(admin.ModelAdmin):
    list_display = ('nom', 'annee', 'date_debut', 'date_fin', 'cloture')


@admin.register(models.Faculte)
class FaculteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'doyen', 'effectif')


@admin.register(models.Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'faculte', 'chef')


@admin.register(models.Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'departement', 'niveau', 'duree_annees')


@admin.register(models.UniteEnseignement)
class UniteEnseignementAdmin(admin.ModelAdmin):
    list_display = ('code', 'nom', 'filiere', 'semestre', 'credits', 'coefficient')


@admin.register(models.Salle)
class SalleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'type', 'capacite')


@admin.register(models.Etudiant)
class EtudiantAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenom', 'sexe', 'statut', 'telephone')


@admin.register(models.Enseignant)
class EnseignantAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenom', 'grade', 'departement', 'telephone')


@admin.register(models.Inscription)
class InscriptionAdmin(admin.ModelAdmin):
    list_display = ('numero', 'etudiant', 'annee', 'filiere', 'statut')


@admin.register(models.Note)
class NoteAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'ue', 'type', 'note')


@admin.register(models.Examen)
class ExamenAdmin(admin.ModelAdmin):
    list_display = ('nom', 'annee', 'date_debut', 'statut')


@admin.register(models.CoursEnLigne)
class CoursEnLigneAdmin(admin.ModelAdmin):
    list_display = ('titre', 'ue', 'enseignant', 'duree_minutes', 'publie')
    list_filter = ('ue', 'publie')


@admin.register(models.Presence)
class PresenceAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'ue', 'date', 'statut')


@admin.register(models.Creneau)
class CreneauAdmin(admin.ModelAdmin):
    list_display = ('ue', 'jour', 'heure_debut', 'heure_fin', 'salle')


@admin.register(models.PlatCantine)
class PlatCantineAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prix', 'calories', 'categorie')


@admin.register(models.MenuJour)
class MenuJourAdmin(admin.ModelAdmin):
    list_display = ('date', 'plat', 'type')


@admin.register(models.CantineCompte)
class CantineCompteAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'solde', 'jour_couvert')


@admin.register(models.RechargeCantine)
class RechargeCantineAdmin(admin.ModelAdmin):
    list_display = ('compte', 'montant', 'date', 'mode')


@admin.register(models.CommandeCantine)
class CommandeCantineAdmin(admin.ModelAdmin):
    list_display = ('compte', 'plat', 'date', 'montant')


@admin.register(models.Bibliographie)
class BibliographieAdmin(admin.ModelAdmin):
    list_display = ('titre', 'auteur', 'domaine', 'disponibles')


@admin.register(models.TypeFrais)
class TypeFraisAdmin(admin.ModelAdmin):
    list_display = ('nom', 'montant', 'periodicite', 'obligatoire')


@admin.register(models.Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = ('reference', 'etudiant', 'montant', 'date', 'mode')


@admin.register(models.Bourse)
class BourseAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'type', 'montant_mensuel', 'date_debut', 'date_fin')


@admin.register(models.ExperienceLabo)
class ExperienceLaboAdmin(admin.ModelAdmin):
    list_display = ('titre', 'discipline', 'niveau', 'difficulte', 'actif')
    list_filter = ('discipline', 'niveau', 'actif')
    prepopulated_fields = {'slug': ('titre',)}


@admin.register(models.RapportExperience)
class RapportExperienceAdmin(admin.ModelAdmin):
    list_display = ('etudiant', 'experience', 'note', 'date')
    list_filter = ('experience',)
