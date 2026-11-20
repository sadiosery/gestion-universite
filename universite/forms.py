from django import forms
from django.utils import timezone

from . import models


class UniversiteParametreForm(forms.ModelForm):
    class Meta:
        model = models.UniversiteParametre
        fields = '__all__'
        widgets = {f: forms.TextInput(attrs={'class': 'form-control'})
                   for f in ['nom_universite', 'sigle', 'slogan', 'recteur', 'telephone', 'email',
                             'site_web', 'devise', 'devise_code']}
        widgets['adresse'] = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        widgets['mention_bulletin'] = forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
        widgets['logo'] = forms.ClearableFileInput(attrs={'class': 'form-control'})


class AnneeAcademiqueForm(forms.ModelForm):
    class Meta:
        model = models.AnneeAcademique
        fields = ['libelle', 'date_debut', 'date_fin', 'active']
        widgets = {
            'libelle': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class SemestreForm(forms.ModelForm):
    class Meta:
        model = models.Semestre
        fields = ['annee', 'type', 'nom', 'date_debut', 'date_fin', 'cloture']
        widgets = {
            'annee': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class FaculteForm(forms.ModelForm):
    class Meta:
        model = models.Faculte
        fields = ['nom', 'code', 'doyen', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'doyen': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DepartementForm(forms.ModelForm):
    class Meta:
        model = models.Departement
        fields = ['faculte', 'nom', 'code', 'chef']
        widgets = {
            'faculte': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'chef': forms.TextInput(attrs={'class': 'form-control'}),
        }


class FiliereForm(forms.ModelForm):
    class Meta:
        model = models.Filiere
        fields = ['departement', 'nom', 'code', 'niveau', 'duree_annees', 'description']
        widgets = {
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'niveau': forms.Select(attrs={'class': 'form-select'}),
            'duree_annees': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class SalleForm(forms.ModelForm):
    class Meta:
        model = models.Salle
        fields = ['nom', 'type', 'capacite', 'equipement']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'capacite': forms.NumberInput(attrs={'class': 'form-control'}),
            'equipement': forms.TextInput(attrs={'class': 'form-control'}),
        }


class EnseignantForm(forms.ModelForm):
    class Meta:
        model = models.Enseignant
        fields = ['nom', 'prenom', 'sexe', 'grade', 'departement', 'specialite',
                  'telephone', 'email', 'adresse', 'date_recrutement', 'salaire_base',
                  'charge_horaire', 'statut', 'photo']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'grade': forms.Select(attrs={'class': 'form-select'}),
            'departement': forms.Select(attrs={'class': 'form-select'}),
            'specialite': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'date_recrutement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salaire_base': forms.NumberInput(attrs={'class': 'form-control'}),
            'charge_horaire': forms.NumberInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class EtudiantForm(forms.ModelForm):
    class Meta:
        model = models.Etudiant
        fields = ['nom', 'prenom', 'sexe', 'date_naissance', 'lieu_naissance', 'nationalite',
                  'telephone', 'email', 'adresse', 'statut', 'boursier', 'photo',
                  'tuteur_nom', 'tuteur_telephone']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'sexe': forms.Select(attrs={'class': 'form-select'}),
            'date_naissance': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu_naissance': forms.TextInput(attrs={'class': 'form-control'}),
            'nationalite': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'adresse': forms.TextInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'tuteur_nom': forms.TextInput(attrs={'class': 'form-control'}),
            'tuteur_telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class InscriptionForm(forms.ModelForm):
    class Meta:
        model = models.Inscription
        fields = ['etudiant', 'annee', 'filiere', 'niveau_annee', 'date', 'statut',
                  'montant_paye', 'note']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'annee': forms.Select(attrs={'class': 'form-select'}),
            'filiere': forms.Select(attrs={'class': 'form-select'}),
            'niveau_annee': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'montant_paye': forms.NumberInput(attrs={'class': 'form-control'}),
            'note': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class UeForm(forms.ModelForm):
    class Meta:
        model = models.UniteEnseignement
        fields = ['code', 'nom', 'filiere', 'semestre', 'credits', 'coefficient',
                  'type', 'volume_horaire', 'description']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'filiere': forms.Select(attrs={'class': 'form-select'}),
            'semestre': forms.Select(attrs={'class': 'form-select'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control'}),
            'coefficient': forms.NumberInput(attrs={'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'volume_horaire': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AffectationUEForm(forms.ModelForm):
    class Meta:
        model = models.AffectationUE
        fields = ['ue', 'enseignant', 'heures_cours', 'heures_td', 'heures_tp']
        widgets = {
            'ue': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'heures_cours': forms.NumberInput(attrs={'class': 'form-control'}),
            'heures_td': forms.NumberInput(attrs={'class': 'form-control'}),
            'heures_tp': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class NoteForm(forms.ModelForm):
    class Meta:
        model = models.Note
        fields = ['etudiant', 'ue', 'type', 'note', 'date']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'ue': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'note': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.25'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class SaisieNotesForm(forms.Form):
    ue = forms.ModelChoiceField(
        queryset=models.UniteEnseignement.objects.all(),
        label='Unité d\'enseignement', widget=forms.Select(attrs={'class': 'form-select'}))


class PresenceForm(forms.ModelForm):
    class Meta:
        model = models.Presence
        fields = ['etudiant', 'ue', 'date', 'statut', 'heure_arrivee', 'justificatif']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'ue': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'heure_arrivee': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'justificatif': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CreneauForm(forms.ModelForm):
    class Meta:
        model = models.Creneau
        fields = ['ue', 'jour', 'heure_debut', 'heure_fin', 'salle', 'type']
        widgets = {
            'ue': forms.Select(attrs={'class': 'form-select'}),
            'jour': forms.Select(attrs={'class': 'form-select'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'heure_fin': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'salle': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
        }


class ExamenForm(forms.ModelForm):
    class Meta:
        model = models.Examen
        fields = ['nom', 'annee', 'session', 'date_debut', 'date_fin', 'statut', 'description']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'annee': forms.Select(attrs={'class': 'form-select'}),
            'session': forms.Select(attrs={'class': 'form-select'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EpreuveExamenForm(forms.ModelForm):
    class Meta:
        model = models.EpreuveExamen
        fields = ['ue', 'date', 'heure_debut', 'duree', 'salle', 'surveillants']
        widgets = {
            'ue': forms.Select(attrs={'class': 'form-select'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'heure_debut': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'duree': forms.NumberInput(attrs={'class': 'form-control'}),
            'salle': forms.Select(attrs={'class': 'form-select'}),
            'surveillants': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
        }


class CoursEnLigneForm(forms.ModelForm):
    class Meta:
        model = models.CoursEnLigne
        fields = ['ue', 'enseignant', 'titre', 'description', 'contenu', 'fichier',
                  'url_video', 'duree_minutes', 'publie']
        widgets = {
            'ue': forms.Select(attrs={'class': 'form-select'}),
            'enseignant': forms.Select(attrs={'class': 'form-select'}),
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'contenu': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
            'url_video': forms.URLInput(attrs={'class': 'form-control'}),
            'duree_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'publie': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class TypeFraisForm(forms.ModelForm):
    class Meta:
        model = models.TypeFrais
        fields = ['nom', 'montant', 'periodicite', 'obligatoire', 'filiere']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'periodicite': forms.Select(attrs={'class': 'form-select'}),
            'filiere': forms.Select(attrs={'class': 'form-select'}),
        }


class PaiementForm(forms.ModelForm):
    class Meta:
        model = models.Paiement
        fields = ['etudiant', 'annee', 'type_frais', 'montant', 'date', 'mode',
                  'reference_externe']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'annee': forms.Select(attrs={'class': 'form-select'}),
            'type_frais': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'mode': forms.Select(attrs={'class': 'form-select'}),
            'reference_externe': forms.TextInput(attrs={'class': 'form-control'}),
        }


class BourseForm(forms.ModelForm):
    class Meta:
        model = models.Bourse
        fields = ['etudiant', 'type', 'montant_mensuel', 'date_debut', 'date_fin', 'actif']
        widgets = {
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'montant_mensuel': forms.NumberInput(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# ---------------------------------------------------------------------------
# Cantine
# ---------------------------------------------------------------------------

class PlatCantineForm(forms.ModelForm):
    class Meta:
        model = models.PlatCantine
        fields = ['nom', 'categorie', 'prix', 'calories', 'proteines', 'glucides',
                  'lipides', 'vegetarien', 'actif']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'prix': forms.NumberInput(attrs={'class': 'form-control'}),
            'calories': forms.NumberInput(attrs={'class': 'form-control'}),
            'proteines': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'glucides': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
            'lipides': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1'}),
        }


class MenuJourForm(forms.ModelForm):
    class Meta:
        model = models.MenuJour
        fields = ['date', 'type', 'plat']
        widgets = {
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'type': forms.Select(attrs={'class': 'form-select'}),
            'plat': forms.Select(attrs={'class': 'form-select'}),
        }


class RechargeCantineForm(forms.ModelForm):
    class Meta:
        model = models.RechargeCantine
        fields = ['compte', 'montant', 'mode']
        widgets = {
            'compte': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control'}),
            'mode': forms.Select(attrs={'class': 'form-select'}),
        }


class CommandeCantineForm(forms.ModelForm):
    class Meta:
        model = models.CommandeCantine
        fields = ['compte', 'plat', 'menu']
        widgets = {
            'compte': forms.Select(attrs={'class': 'form-select'}),
            'plat': forms.Select(attrs={'class': 'form-select'}),
            'menu': forms.Select(attrs={'class': 'form-select'}),
        }


class BibliographieForm(forms.ModelForm):
    class Meta:
        model = models.Bibliographie
        fields = ['titre', 'auteur', 'isbn', 'domaine', 'emplacement', 'quantite', 'annee_edition']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'auteur': forms.TextInput(attrs={'class': 'form-control'}),
            'isbn': forms.TextInput(attrs={'class': 'form-control'}),
            'domaine': forms.Select(attrs={'class': 'form-select'}),
            'emplacement': forms.TextInput(attrs={'class': 'form-control'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control'}),
            'annee_edition': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class PretOuvrageForm(forms.ModelForm):
    class Meta:
        model = models.PretOuvrage
        fields = ['ouvrage', 'etudiant', 'date_pret', 'date_retour_prevue']
        widgets = {
            'ouvrage': forms.Select(attrs={'class': 'form-select'}),
            'etudiant': forms.Select(attrs={'class': 'form-select'}),
            'date_pret': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_retour_prevue': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


# ---------------------------------------------------------------------------
# Laboratoire virtuel
# ---------------------------------------------------------------------------

class ExperienceLaboForm(forms.ModelForm):
    class Meta:
        model = models.ExperienceLabo
        fields = ['titre', 'slug', 'discipline', 'duree_minutes', 'objectif',
                  'protocole', 'consignes', 'actif']
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'discipline': forms.Select(attrs={'class': 'form-select'}),
            'duree_minutes': forms.NumberInput(attrs={'class': 'form-control'}),
            'objectif': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'protocole': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'consignes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class RapportExperienceForm(forms.ModelForm):
    class Meta:
        model = models.RapportExperience
        fields = ['experience', 'parametres', 'resultats', 'observations']
        widgets = {
            'experience': forms.Select(attrs={'class': 'form-select'}),
            'parametres': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'resultats': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
