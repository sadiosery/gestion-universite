from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def generer_reference(prefixe, modele, champ='reference'):
    """Génère une référence séquentielle : PRÉFIXE/ANNÉE/NNNN"""
    annee = timezone.now().year
    cls = globals().get(modele)
    derniere = cls.objects.filter(**{f'{champ}__startswith': f'{prefixe}/{annee}/'}).order_by('-id').first()
    numero = 1
    if derniere:
        numero = int(getattr(derniere, champ).rsplit('/', 1)[-1]) + 1
    return f'{prefixe}/{annee}/{numero:04d}'


def _annee_courante():
    annee = AnneeAcademique.objects.filter(active=True).first()
    if annee:
        return annee
    return AnneeAcademique.objects.order_by('-id').first()


# ---------------------------------------------------------------------------
# Paramétrage & calendrier académique
# ---------------------------------------------------------------------------

class UniversiteParametre(models.Model):
    nom_universite = models.CharField(max_length=200, default='UNIVERSITÉ')
    sigle = models.CharField(max_length=50, blank=True)
    slogan = models.CharField(max_length=200, blank=True)
    recteur = models.CharField(max_length=150, blank=True)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    site_web = models.CharField(max_length=100, blank=True)
    logo = models.ImageField(upload_to='universite/', blank=True, null=True)
    devise = models.CharField(max_length=20, default='F CFA')
    devise_code = models.CharField(max_length=5, default='FCFA')
    note_maximale = models.DecimalField('Note maximale', max_digits=4, decimal_places=2, default=Decimal('20.00'))
    seuil_validation = models.DecimalField('Seuil de validation UE', max_digits=4, decimal_places=2, default=Decimal('10.00'))
    credit_annee = models.PositiveIntegerField('Crédits par année', default=60)
    mention_bulletin = models.TextField(blank=True)

    class Meta:
        verbose_name = "Paramètre d'université"
        verbose_name_plural = "Paramètres d'université"

    def __str__(self):
        return self.nom_universite

    @classmethod
    def obtenir(cls):
        parametre, _ = cls.objects.get_or_create(pk=1)
        return parametre


class AnneeAcademique(models.Model):
    libelle = models.CharField('Année académique', max_length=50, unique=True, help_text='Ex : 2025-2026')
    date_debut = models.DateField()
    date_fin = models.DateField()
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Année académique'
        verbose_name_plural = 'Années académiques'
        ordering = ['-date_debut']

    def __str__(self):
        return self.libelle

    def save(self, *args, **kwargs):
        if self.active:
            AnneeAcademique.objects.filter(active=True).exclude(pk=self.pk).update(active=False)
        super().save(*args, **kwargs)

    @classmethod
    def en_cours(cls):
        return cls.objects.filter(active=True).first() or cls.objects.order_by('-id').first()


class Semestre(models.Model):
    TYPES = (('S1', 'S1'), ('S2', 'S2'), ('S3', 'S3'), ('S4', 'S4'),
             ('S5', 'S5'), ('S6', 'S6'), ('S7', 'S7'), ('S8', 'S8'),
             ('S9', 'S9'), ('S10', 'S10'))
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.CASCADE, related_name='semestres')
    type = models.CharField(max_length=5, choices=TYPES, default='S1')
    nom = models.CharField(max_length=50, default='Semestre 1')
    date_debut = models.DateField()
    date_fin = models.DateField()
    cloture = models.BooleanField('Semestre clôturé', default=False)

    class Meta:
        verbose_name = 'Semestre'
        verbose_name_plural = 'Semestres'
        ordering = ['annee', 'type']
        unique_together = ('annee', 'type')

    def __str__(self):
        return f'{self.nom} — {self.annee.libelle}'

    def save(self, *args, **kwargs):
        if not self.nom or self.nom == 'Semestre 1':
            self.nom = f'Semestre {self.type}'
        super().save(*args, **kwargs)

    @property
    def credits(self):
        return sum(ue.credits for ue in self.ues.all())


# ---------------------------------------------------------------------------
# Organisation : facultés, départements, filières, salles
# ---------------------------------------------------------------------------

class Faculte(models.Model):
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    doyen = models.CharField(max_length=150, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Faculté'
        verbose_name_plural = 'Facultés'
        ordering = ['nom']

    def __str__(self):
        return self.nom

    @property
    def effectif(self):
        return Etudiant.objects.filter(inscriptions__filiere__departement__faculte=self).distinct().count()


class Departement(models.Model):
    faculte = models.ForeignKey(Faculte, on_delete=models.CASCADE, related_name='departements')
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    chef = models.CharField(max_length=150, blank=True)

    class Meta:
        verbose_name = 'Département'
        verbose_name_plural = 'Départements'
        ordering = ['nom']

    def __str__(self):
        return f'{self.nom} ({self.faculte})'


class Filiere(models.Model):
    NIVEAUX = (
        ('Licence', 'Licence'),
        ('Master', 'Master'),
        ('Doctorat', 'Doctorat'),
    )
    departement = models.ForeignKey(Departement, on_delete=models.CASCADE, related_name='filieres')
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=20, blank=True)
    niveau = models.CharField(max_length=20, choices=NIVEAUX, default='Licence')
    duree_annees = models.PositiveIntegerField('Durée (années)', default=3)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Filière / Programme'
        verbose_name_plural = 'Filières / Programmes'
        ordering = ['nom']

    def __str__(self):
        return f'{self.nom} ({self.code})'

    @property
    def effectif(self):
        return Inscription.objects.filter(filiere=self, statut='active').count()


class Salle(models.Model):
    TYPES = (
        ('cours', 'Salle de cours'),
        ('td', 'Salle de TD'),
        ('tp', 'Laboratoire / TP'),
        ('amphi', 'Amphithéâtre'),
        ('informatique', 'Salle informatique'),
    )
    nom = models.CharField(max_length=50, unique=True)
    type = models.CharField(max_length=20, choices=TYPES, default='cours')
    capacite = models.PositiveIntegerField('Capacité', default=50)
    equipement = models.CharField(max_length=200, blank=True)

    class Meta:
        verbose_name = 'Salle'
        verbose_name_plural = 'Salles'
        ordering = ['nom']

    def __str__(self):
        return self.nom


# ---------------------------------------------------------------------------
# Enseignants
# ---------------------------------------------------------------------------

class Enseignant(models.Model):
    GRADES = (
        ('Assistant', 'Assistant'),
        ('Assistant Maître-assistant', 'Assistant Maître-assistant'),
        ('Maître-assistant', 'Maître-assistant'),
        ('Maître de conférences', 'Maître de conférences'),
        ('Professeur titulaire', 'Professeur titulaire'),
        ('Chargé de cours', 'Chargé de cours'),
        ('Attaché de recherche', 'Attaché de recherche'),
    )
    SEXES = (('M', 'Masculin'), ('F', 'Féminin'))
    STATUTS = (('actif', 'Actif'), ('conge', 'En congé'), ('inactif', 'Inactif'))

    matricule = models.CharField(max_length=50, unique=True, blank=True)
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    sexe = models.CharField(max_length=1, choices=SEXES)
    grade = models.CharField(max_length=40, choices=GRADES, default='Chargé de cours')
    departement = models.ForeignKey(Departement, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='enseignants')
    specialite = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    adresse = models.CharField(max_length=250, blank=True)
    photo = models.ImageField(upload_to='enseignants/', blank=True, null=True)
    date_recrutement = models.DateField(default=timezone.now)
    salaire_base = models.DecimalField('Salaire de base', max_digits=12, decimal_places=2, default=0)
    charge_horaire = models.PositiveIntegerField('Charge horaire / an', default=0)
    statut = models.CharField(max_length=20, choices=STATUTS, default='actif')
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Enseignant'
        verbose_name_plural = 'Enseignants'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f'{self.nom} {self.prenom}'

    @property
    def nom_complet(self):
        return f'{self.nom} {self.prenom}'

    @property
    def nb_ues(self):
        return self.affectations.count()

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.matricule = generer_reference('ENS', 'Enseignant', 'matricule')
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------------
# Étudiants & inscriptions
# ---------------------------------------------------------------------------

class Etudiant(models.Model):
    SEXES = (('M', 'Masculin'), ('F', 'Féminin'))
    STATUTS = (
        ('actif', 'Actif'),
        ('en_conge', 'En congé'),
        ('suspendu', 'Suspendu'),
        ('radie', 'Radié'),
        ('diplome', 'Diplômé'),
        ('exclu', 'Exclu'),
    )
    matricule = models.CharField(max_length=50, unique=True, blank=True)
    nom = models.CharField(max_length=150)
    prenom = models.CharField(max_length=150)
    sexe = models.CharField(max_length=1, choices=SEXES)
    date_naissance = models.DateField()
    lieu_naissance = models.CharField(max_length=100, blank=True)
    nationalite = models.CharField(max_length=100, default='Ivoirienne')
    photo = models.ImageField(upload_to='etudiants/', blank=True, null=True)
    adresse = models.CharField(max_length=250, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='actif')
    boursier = models.BooleanField(default=False)
    date_inscription = models.DateField(default=timezone.now)

    tuteur_nom = models.CharField('Nom du parent / tuteur', max_length=200, blank=True)
    tuteur_telephone = models.CharField('Téléphone du tuteur', max_length=30, blank=True)

    user = models.OneToOneField('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='etudiant', verbose_name='Compte utilisateur')
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True, related_name='etudiants')

    class Meta:
        verbose_name = 'Étudiant'
        verbose_name_plural = 'Étudiants'
        ordering = ['nom', 'prenom']

    def __str__(self):
        return f'{self.nom} {self.prenom}'

    @property
    def nom_complet(self):
        return f'{self.nom} {self.prenom}'

    @property
    def age(self):
        if not self.date_naissance:
            return None
        return (timezone.now().date() - self.date_naissance).days // 365

    def save(self, *args, **kwargs):
        if not self.matricule:
            self.matricule = generer_reference('ETU', 'Etudiant', 'matricule')
        super().save(*args, **kwargs)

    def inscription_courante(self):
        return self.inscriptions.filter(annee=_annee_courante()).first()


class Inscription(models.Model):
    STATUTS = (
        ('en_attente', 'En attente'),
        ('active', 'Active'),
        ('cloturee', 'Clôturée'),
        ('abandon', 'Abandon'),
    )
    numero = models.CharField(max_length=50, unique=True, blank=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='inscriptions')
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.PROTECT, related_name='inscriptions')
    filiere = models.ForeignKey(Filiere, on_delete=models.PROTECT, related_name='inscriptions')
    niveau_annee = models.PositiveIntegerField('Niveau (année d\'étude)', default=1)
    date = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUTS, default='active')
    montant_paye = models.DecimalField('Montant payé à l\'inscription', max_digits=12, decimal_places=2, default=0)
    note = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Inscription'
        verbose_name_plural = 'Inscriptions'
        ordering = ['-date']
        constraints = [
            models.UniqueConstraint(fields=['etudiant', 'annee'], name='unique_etudiant_annee_uni')
        ]

    def __str__(self):
        return f'{self.numero} — {self.etudiant}'

    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = generer_reference('INS', 'Inscription', 'numero')
        super().save(*args, **kwargs)
        self.etudiant.filiere = self.filiere
        self.etudiant.save(update_fields=['filiere'])


# ---------------------------------------------------------------------------
# Unités d'enseignement (UE) & affectations
# ---------------------------------------------------------------------------

class UniteEnseignement(models.Model):
    TYPES = (
        ('fondamentale', 'Fondamentale'),
        ('majeure', 'Majeure'),
        ('transversale', 'Transversale'),
        ('optionnelle', 'Optionnelle'),
        ('professionnelle', 'Professionnelle'),
    )
    code = models.CharField(max_length=20, unique=True)
    nom = models.CharField(max_length=250)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='ues')
    semestre = models.ForeignKey(Semestre, on_delete=models.CASCADE, related_name='ues')
    credits = models.PositiveIntegerField('Crédits (ECTS)', default=3)
    coefficient = models.DecimalField(max_digits=4, decimal_places=2, default=Decimal('1.00'))
    type = models.CharField(max_length=20, choices=TYPES, default='fondamentale')
    volume_horaire = models.PositiveIntegerField('Volume horaire', default=30)
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Unité d\'enseignement'
        verbose_name_plural = 'Unités d\'enseignement'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} — {self.nom}'

    @property
    def responsable(self):
        affect = self.affectations.first()
        return affect.enseignant if affect else None


class AffectationUE(models.Model):
    ue = models.ForeignKey(UniteEnseignement, on_delete=models.CASCADE, related_name='affectations')
    enseignant = models.ForeignKey(Enseignant, on_delete=models.CASCADE, related_name='affectations')
    heures_cours = models.PositiveIntegerField('Heures de cours', default=0)
    heures_td = models.PositiveIntegerField('Heures de TD', default=0)
    heures_tp = models.PositiveIntegerField('Heures de TP', default=0)

    class Meta:
        verbose_name = 'Affectation d\'UE'
        verbose_name_plural = 'Affectations d\'UE'
        unique_together = ('ue', 'enseignant')

    def __str__(self):
        return f'{self.enseignant} → {self.ue}'

    @property
    def total_heures(self):
        return self.heures_cours + self.heures_td + self.heures_tp


# ---------------------------------------------------------------------------
# Cours en ligne
# ---------------------------------------------------------------------------

class CoursEnLigne(models.Model):
    ue = models.ForeignKey(UniteEnseignement, on_delete=models.CASCADE, related_name='cours')
    enseignant = models.ForeignKey(Enseignant, on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='cours')
    titre = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    contenu = models.TextField('Contenu du cours', blank=True)
    fichier = models.FileField('Fichier / support de cours', upload_to='cours/', blank=True, null=True)
    url_video = models.URLField('Lien vidéo ou ressource en ligne', blank=True)
    duree_minutes = models.PositiveIntegerField('Durée (minutes)', default=60)
    publie = models.BooleanField('Publié aux étudiants', default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Cours en ligne'
        verbose_name_plural = 'Cours en ligne'
        ordering = ['ue', 'titre']

    def __str__(self):
        return f'{self.ue.code} — {self.titre}'


# ---------------------------------------------------------------------------
# Évaluation : notes, délibérations
# ---------------------------------------------------------------------------

class Note(models.Model):
    TYPES = (
        ('CC', 'Contrôle continu'),
        ('TP', 'Travaux pratiques'),
        ('EX', 'Examen final'),
        ('RAT', 'Rattrapage'),
    )
    POIDS = {'CC': 1, 'TP': 1, 'EX': 2, 'RAT': 1}

    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='notes')
    ue = models.ForeignKey(UniteEnseignement, on_delete=models.CASCADE, related_name='notes')
    type = models.CharField(max_length=5, choices=TYPES, default='EX')
    note = models.DecimalField('Note / 20', max_digits=4, decimal_places=2)
    date = models.DateField(default=timezone.now)
    apprecie = models.CharField(max_length=100, blank=True)

    class Meta:
        verbose_name = 'Note'
        verbose_name_plural = 'Notes'
        ordering = ['ue', 'etudiant', 'date']

    def __str__(self):
        return f'{self.etudiant} — {self.ue} : {self.note}/20'

    def clean(self):
        if self.note is not None and (self.note < 0 or self.note > 20):
            raise ValidationError('La note doit être comprise entre 0 et 20.')

    def save(self, *args, **kwargs):
        if not self.apprecie:
            self.apprecie = apprecier(self.note)
        super().save(*args, **kwargs)


class ValidationUE(models.Model):
    DECISIONS = (
        ('valide', 'Validée'),
        ('compense', 'Compensée'),
        ('echoue', 'Échouée'),
        ('credit', 'Crédit acquis'),
    )
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='validations')
    ue = models.ForeignKey(UniteEnseignement, on_delete=models.CASCADE, related_name='validations')
    semestre = models.ForeignKey(Semestre, on_delete=models.CASCADE, related_name='validations')
    moyenne = models.DecimalField('Moyenne / 20', max_digits=4, decimal_places=2, default=0)
    decision = models.CharField(max_length=20, choices=DECISIONS, default='echoue')
    session = models.CharField('Session', max_length=20, default='Normale')

    class Meta:
        verbose_name = 'Validation d\'UE'
        verbose_name_plural = 'Validations d\'UE'
        unique_together = ('etudiant', 'ue', 'semestre')

    def __str__(self):
        return f'{self.etudiant} — {self.ue} : {self.moyenne} ({self.get_decision_display()})'


def apprecier(note):
    note = float(note)
    if note >= 16:
        return 'Excellent'
    if note >= 14:
        return 'Très bien'
    if note >= 12:
        return 'Bien'
    if note >= 10:
        return 'Passable'
    if note >= 8:
        return 'Insuffisant'
    if note >= 6:
        return 'Médiocre'
    return 'Très insuffisant'


# ---------------------------------------------------------------------------
# Présences & emploi du temps
# ---------------------------------------------------------------------------

class Presence(models.Model):
    STATUTS = (
        ('Present', 'Présent'),
        ('Absent', 'Absent'),
        ('Retard', 'Retard'),
        ('Excuse', 'Excusé'),
    )
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='presences')
    ue = models.ForeignKey(UniteEnseignement, on_delete=models.CASCADE, related_name='presences')
    date = models.DateField(default=timezone.now)
    statut = models.CharField(max_length=20, choices=STATUTS, default='Present')
    heure_arrivee = models.TimeField(blank=True, null=True)
    justificatif = models.CharField(max_length=250, blank=True)

    class Meta:
        verbose_name = 'Présence'
        verbose_name_plural = 'Présences'
        ordering = ['-date']
        unique_together = ('etudiant', 'ue', 'date')

    def __str__(self):
        return f'{self.etudiant} — {self.ue} : {self.statut}'


class Creneau(models.Model):
    JOURS = (
        ('Lundi', 'Lundi'), ('Mardi', 'Mardi'), ('Mercredi', 'Mercredi'),
        ('Jeudi', 'Jeudi'), ('Vendredi', 'Vendredi'), ('Samedi', 'Samedi'),
    )
    ue = models.ForeignKey(UniteEnseignement, on_delete=models.CASCADE, related_name='creneaux')
    jour = models.CharField(max_length=10, choices=JOURS)
    heure_debut = models.TimeField()
    heure_fin = models.TimeField()
    salle = models.ForeignKey(Salle, on_delete=models.SET_NULL, null=True, blank=True, related_name='creneaux')
    type = models.CharField('Type de séance', max_length=10, choices=Note.TYPES[:3], default='CC')

    class Meta:
        verbose_name = 'Créneau (emploi du temps)'
        verbose_name_plural = 'Emplois du temps'
        ordering = ['jour', 'heure_debut']

    def __str__(self):
        return f'{self.ue} — {self.jour} {self.heure_debut:%H:%M}-{self.heure_fin:%H:%M}'


# ---------------------------------------------------------------------------
# Examens & convocations
# ---------------------------------------------------------------------------

class Examen(models.Model):
    STATUTS = (
        ('programme', 'Programmé'),
        ('en_cours', 'En cours'),
        ('termine', 'Terminé'),
        ('annule', 'Annulé'),
    )
    SESSIONS = (('Normale', 'Normale'), ('Rattrapage', 'Rattrapage'))
    nom = models.CharField(max_length=150)
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.CASCADE, related_name='examens')
    session = models.CharField(max_length=20, choices=SESSIONS, default='Normale')
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='programme')
    description = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Examen'
        verbose_name_plural = 'Examens'
        ordering = ['-date_debut']

    def __str__(self):
        return f'{self.nom} ({self.session})'


class EpreuveExamen(models.Model):
    examen = models.ForeignKey(Examen, on_delete=models.CASCADE, related_name='epreuves')
    ue = models.ForeignKey(UniteEnseignement, on_delete=models.CASCADE, related_name='epreuves')
    date = models.DateField()
    heure_debut = models.TimeField(default=timezone.now)
    duree = models.PositiveIntegerField('Durée (minutes)', default=120)
    salle = models.ForeignKey(Salle, on_delete=models.SET_NULL, null=True, blank=True, related_name='epreuves')
    surveillants = models.ManyToManyField(Enseignant, related_name='surveillances', blank=True)

    class Meta:
        verbose_name = 'Épreuve d\'examen'
        verbose_name_plural = 'Épreuves d\'examens'
        ordering = ['date', 'heure_debut']

    def __str__(self):
        return f'{self.examen} — {self.ue}'


class Convocation(models.Model):
    epreuve = models.ForeignKey(EpreuveExamen, on_delete=models.CASCADE, related_name='convocations')
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='convocations')
    present = models.BooleanField('Présent à l\'épreuve', default=False)
    note_epreuve = models.DecimalField('Note de l\'épreuve', max_digits=4, decimal_places=2,
                                       null=True, blank=True)

    class Meta:
        verbose_name = 'Convocation'
        verbose_name_plural = 'Convocations'
        unique_together = ('epreuve', 'etudiant')

    def __str__(self):
        return f'{self.etudiant} → {self.epreuve}'


# ---------------------------------------------------------------------------
# Scolarité : frais, paiements, bourses
# ---------------------------------------------------------------------------

class TypeFrais(models.Model):
    PERIODICITES = (
        ('inscription', 'Inscription'),
        ('annuel', 'Annuel'),
        ('semestriel', 'Semestriel'),
        ('mensuel', 'Mensuel'),
        ('unique', 'Unique'),
    )
    nom = models.CharField(max_length=100)
    montant = models.DecimalField('Montant par défaut', max_digits=12, decimal_places=2, default=0)
    periodicite = models.CharField(max_length=20, choices=PERIODICITES, default='annuel')
    obligatoire = models.BooleanField(default=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='types_frais', verbose_name='Filière (optionnel)')

    class Meta:
        verbose_name = 'Type de frais'
        verbose_name_plural = 'Types de frais'
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Paiement(models.Model):
    MODES = (
        ('Especes', 'Espèces'),
        ('Mobile Money', 'Mobile Money'),
        ('Virement', 'Virement bancaire'),
        ('Cheque', 'Chèque'),
        ('Carte', 'Carte bancaire'),
    )
    reference = models.CharField(max_length=50, unique=True, blank=True)
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='paiements')
    annee = models.ForeignKey(AnneeAcademique, on_delete=models.PROTECT, related_name='paiements')
    type_frais = models.ForeignKey(TypeFrais, on_delete=models.PROTECT, related_name='paiements')
    montant = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField(default=timezone.now)
    mode = models.CharField(max_length=20, choices=MODES, default='Especes')
    reference_externe = models.CharField('Référence externe', max_length=100, blank=True)
    enregistre_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True,
                                       related_name='paiements_universite')

    class Meta:
        verbose_name = 'Paiement'
        verbose_name_plural = 'Paiements'
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.reference} — {self.etudiant}'

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generer_reference('PAY', 'Paiement')
        super().save(*args, **kwargs)


class Bourse(models.Model):
    TYPES = (
        ('excellence', 'Excellence'),
        ('merite', 'Mérite'),
        ('sociale', 'Sociale'),
        ('etat', 'Bourse d\'État'),
        ('privee', 'Bourse privée'),
    )
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='bourses')
    type = models.CharField(max_length=20, choices=TYPES, default='etat')
    montant_mensuel = models.DecimalField('Montant mensuel', max_digits=12, decimal_places=2, default=0)
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Bourse'
        verbose_name_plural = 'Bourses'
        ordering = ['-date_debut']

    def __str__(self):
        return f'{self.etudiant} — {self.get_type_display()}'


# ---------------------------------------------------------------------------
# Cantine universitaire
# ---------------------------------------------------------------------------

class PlatCantine(models.Model):
    CATEGORIES = (
        ('entree', 'Entrée'),
        ('plat', 'Plat principal'),
        ('accompagnement', 'Accompagnement'),
        ('dessert', 'Dessert'),
        ('boisson', 'Boisson'),
    )
    nom = models.CharField(max_length=150)
    categorie = models.CharField(max_length=20, choices=CATEGORIES, default='plat')
    prix = models.DecimalField('Prix', max_digits=8, decimal_places=2, default=0)
    calories = models.PositiveIntegerField('Calories (kcal)', default=0)
    proteines = models.DecimalField('Protéines (g)', max_digits=6, decimal_places=1, default=0)
    glucides = models.DecimalField('Glucides (g)', max_digits=6, decimal_places=1, default=0)
    lipides = models.DecimalField('Lipides (g)', max_digits=6, decimal_places=1, default=0)
    vegetarien = models.BooleanField(default=False)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Plat de cantine'
        verbose_name_plural = 'Plats de cantine'
        ordering = ['categorie', 'nom']

    def __str__(self):
        return self.nom

    @property
    def apport_total(self):
        return self.proteines + self.glucides + self.lipides


class MenuJour(models.Model):
    TYPES = (
        ('petit_dejeuner', 'Petit-déjeuner'),
        ('dejeuner', 'Déjeuner'),
        ('diner', 'Dîner'),
    )
    date = models.DateField()
    type = models.CharField(max_length=20, choices=TYPES, default='dejeuner')
    plat = models.ForeignKey(PlatCantine, on_delete=models.CASCADE, related_name='menus')

    class Meta:
        verbose_name = 'Menu du jour'
        verbose_name_plural = 'Menus du jour'
        ordering = ['date', 'type']
        unique_together = ('date', 'type', 'plat')

    def __str__(self):
        return f'{self.date} — {self.get_type_display()} : {self.plat}'


class CantineCompte(models.Model):
    etudiant = models.OneToOneField(Etudiant, on_delete=models.CASCADE, related_name='cantine')
    solde = models.DecimalField('Solde', max_digits=10, decimal_places=2, default=0)
    code_carte = models.CharField('Code carte', max_length=20, unique=True, blank=True)
    actif = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Compte cantine'
        verbose_name_plural = 'Comptes cantine'

    def __str__(self):
        return f'{self.etudiant} — {self.solde} F'

    def save(self, *args, **kwargs):
        if not self.code_carte:
            self.code_carte = generer_reference('CANT', 'CantineCompte', 'code_carte')
        super().save(*args, **kwargs)

    @property
    def jour_couvert(self):
        menu = MenuJour.objects.filter(date=timezone.now().date(), type='dejeuner').first()
        if menu and self.solde >= menu.plat.prix:
            return True
        return False


class RechargeCantine(models.Model):
    MODES = (
        ('Especes', 'Espèces'),
        ('Mobile Money', 'Mobile Money'),
        ('Virement', 'Virement'),
    )
    compte = models.ForeignKey(CantineCompte, on_delete=models.CASCADE, related_name='recharges')
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    mode = models.CharField(max_length=20, choices=MODES, default='Especes')
    reference = models.CharField(max_length=50, blank=True)
    enregistre_par = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        verbose_name = 'Recharge de compte cantine'
        verbose_name_plural = 'Recharges de comptes cantine'
        ordering = ['-date']

    def __str__(self):
        return f'+{self.montant} → {self.compte}'


class CommandeCantine(models.Model):
    compte = models.ForeignKey(CantineCompte, on_delete=models.CASCADE, related_name='commandes')
    plat = models.ForeignKey(PlatCantine, on_delete=models.CASCADE, related_name='commandes')
    menu = models.ForeignKey(MenuJour, on_delete=models.SET_NULL, null=True, blank=True, related_name='commandes')
    date = models.DateTimeField(auto_now_add=True)
    montant = models.DecimalField(max_digits=10, decimal_places=2)
    annule = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Commande cantine'
        verbose_name_plural = 'Commandes cantine'
        ordering = ['-date']

    def __str__(self):
        return f'{self.compte} — {self.plat}'


# ---------------------------------------------------------------------------
# Bibliothèque universitaire
# ---------------------------------------------------------------------------

class Bibliographie(models.Model):
    DOMAINES = (
        ('sciences', 'Sciences'),
        ('technologie', 'Technologie'),
        ('ingenierie', 'Ingénierie'),
        ('mathematiques', 'Mathématiques'),
        ('litterature', 'Littérature'),
        ('droit', 'Droit'),
        ('economie', 'Économie'),
        ('medecine', 'Médecine'),
        ('autre', 'Autre'),
    )
    titre = models.CharField(max_length=250)
    auteur = models.CharField(max_length=200, blank=True)
    isbn = models.CharField(max_length=50, blank=True)
    domaine = models.CharField(max_length=20, choices=DOMAINES, default='sciences')
    emplacement = models.CharField(max_length=50, blank=True)
    quantite = models.PositiveIntegerField('Quantité totale', default=1)
    annee_edition = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        verbose_name = 'Ouvrage'
        verbose_name_plural = 'Ouvrages'
        ordering = ['titre']

    def __str__(self):
        return self.titre

    @property
    def prets_en_cours(self):
        return self.prets.filter(statut='en_cours').count()

    @property
    def disponibles(self):
        return max(self.quantite - self.prets_en_cours, 0)


class PretOuvrage(models.Model):
    STATUTS = (('en_cours', 'En cours'), ('rendu', 'Rendu'), ('retard', 'En retard'))
    ouvrage = models.ForeignKey(Bibliographie, on_delete=models.CASCADE, related_name='prets')
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='prets')
    date_pret = models.DateField(default=timezone.now)
    date_retour_prevue = models.DateField()
    date_retour_reel = models.DateField(blank=True, null=True)
    statut = models.CharField(max_length=20, choices=STATUTS, default='en_cours')

    class Meta:
        verbose_name = 'Prêt d\'ouvrage'
        verbose_name_plural = 'Prêts d\'ouvrages'
        ordering = ['-date_pret']

    def __str__(self):
        return f'{self.ouvrage} → {self.etudiant}'

    @property
    def en_retard(self):
        return self.statut == 'en_cours' and self.date_retour_prevue < timezone.now().date()


# ---------------------------------------------------------------------------
# Laboratoire virtuel interactif
# ---------------------------------------------------------------------------

class ExperienceLabo(models.Model):
    DISCIPLINES = (
        ('physique', 'Physique'),
        ('chimie', 'Chimie'),
        ('biologie', 'Biologie'),
    )
    NIVEAUX = (
        ('L1', 'Licence 1'), ('L2', 'Licence 2'), ('L3', 'Licence 3'),
        ('M1', 'Master 1'), ('M2', 'Master 2'),
    )
    DIFFICULTES = (
        (1, '★ Facile'), (2, '★★ Moyen'), (3, '★★★ Avancé'),
    )
    PICTOGRAMMES = {
        'toxique': ('Toxique', 'bi-emoji-skull', 'danger'),
        'corrosif': ('Corrosif', 'bi-droplet-half', 'danger'),
        'inflammable': ('Inflammable', 'bi-fire', 'warning'),
        'irritant': ('Irritant', 'bi-exclamation-triangle', 'warning'),
        'environnement': ('Danger environnement', 'bi-globe', 'success'),
        'rayonnement': ('Rayonnement', 'bi-radioactive', 'warning'),
        'electrique': ('Risque électrique', 'bi-lightning-charge', 'warning'),
        'biologique': ('Risque biologique', 'bi-virus', 'danger'),
        'port_obligatoire': ('Lunettes & gants', 'bi-eyedropper', 'info'),
    }
    titre = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    discipline = models.CharField(max_length=20, choices=DISCIPLINES, default='physique')
    niveau = models.CharField('Niveau d\'étude', max_length=5, choices=NIVEAUX, default='L1')
    difficulte = models.PositiveSmallIntegerField('Difficulté', choices=DIFFICULTES, default=1)
    duree_minutes = models.PositiveIntegerField('Durée estimée (min)', default=15)
    objectif = models.TextField('Objectif pédagogique')
    protocole = models.TextField('Protocole', blank=True)
    consignes = models.TextField('Consignes de sécurité', blank=True)
    pictogrammes = models.CharField('Pictogrammes de sécurité', max_length=150, blank=True,
                                    help_text='Codes séparés par des virgules : toxique, corrosif, inflammable…')
    materiel = models.TextField('Matériel (un par ligne)', blank=True)
    notions = models.TextField('Notions clés', blank=True)
    formule = models.CharField('Formule théorique', max_length=300, blank=True)
    competences = models.TextField('Compétences visées', blank=True)
    actif = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Expérience du laboratoire virtuel'
        verbose_name_plural = 'Expériences du laboratoire virtuel'
        ordering = ['discipline', 'niveau', 'titre']

    def __str__(self):
        return self.titre

    @property
    def pictos_liste(self):
        return [self.PICTOGRAMMES.get(code.strip()) for code in self.pictogrammes.split(',') if code.strip() in self.PICTOGRAMMES]

    @property
    def materiel_liste(self):
        return [l for l in (self.materiel or '').splitlines() if l.strip()]

    @property
    def notions_liste(self):
        return [n for n in (self.notions or '').splitlines() if n.strip()]

    @property
    def competences_liste(self):
        return [c for c in (self.competences or '').splitlines() if c.strip()]


class RapportExperience(models.Model):
    etudiant = models.ForeignKey(Etudiant, on_delete=models.CASCADE, related_name='rapports_labo')
    experience = models.ForeignKey(ExperienceLabo, on_delete=models.CASCADE, related_name='rapports')
    parametres = models.TextField('Paramètres de la simulation', blank=True)
    donnees = models.TextField('Données de mesure (CSV)', blank=True)
    analyse = models.TextField('Analyse des données', blank=True)
    resultats = models.TextField('Résultats observés', blank=True)
    observations = models.TextField(blank=True)
    conclusion = models.TextField('Conclusion', blank=True)
    note = models.DecimalField('Note', max_digits=4, decimal_places=2, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Rapport d\'expérience'
        verbose_name_plural = 'Rapports d\'expérience'
        ordering = ['-date']

    def __str__(self):
        return f'{self.etudiant} — {self.experience}'


class Page(models.Model):
    """Page de l'application dont on peut restreindre la visibilité par utilisateur."""
    code = models.SlugField('Code', max_length=50, unique=True)
    titre = models.CharField('Titre', max_length=120)
    url_name = models.CharField('Route principale', max_length=100)
    section = models.CharField('Section', max_length=60, blank=True)
    utilisateurs = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name='pages_visibles', blank=True)

    class Meta:
        verbose_name = 'Page'
        verbose_name_plural = 'Pages'
        ordering = ['section', 'titre']

    def __str__(self):
        return self.titre


class Sauvegarde(models.Model):
    """Trace d'une sauvegarde exploitables (fichier .zip autonome)."""
    fichier = models.CharField('Fichier', max_length=255, unique=True)
    taille_octets = models.PositiveBigIntegerField('Taille (octets)', default=0)
    automatique = models.BooleanField('Sauvegarde automatique', default=False)
    date = models.DateTimeField('Date', auto_now_add=True)

    class Meta:
        verbose_name = 'Sauvegarde'
        verbose_name_plural = 'Sauvegardes'
        ordering = ['-date']

    def __str__(self):
        return self.fichier

    @property
    def taille_lisible(self):
        taille = self.taille_octets
        for unite in ('o', 'Ko', 'Mo', 'Go'):
            if taille < 1024:
                return f'{taille:.1f} {unite}'
            taille /= 1024
        return f'{taille:.1f} To'



