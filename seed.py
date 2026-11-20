"""Données de démonstration pour UniversitéGest. Usage : python seed.py"""
import os
from datetime import date, time, timedelta
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from django.contrib.auth.models import Group, User
from django.utils import timezone

from universite.models import (
    AffectationUE, AnneeAcademique, Bibliographie, Bourse, CantineCompte,
    CommandeCantine, Convocation, Creneau, Departement, Enseignant, Etudiant,
    EpreuveExamen, Examen, ExperienceLabo, Faculte, Filiere, Inscription,
    MenuJour, Note, Paiement, PlatCantine, Presence, PretOuvrage,
    RapportExperience, RechargeCantine, Salle, Semestre, TypeFrais,
    UniteEnseignement, UniversiteParametre, ValidationUE,
)

# --- Reset des données université existantes (seed ré-exécutable) ---
RapportExperience.objects.all().delete()
ExperienceLabo.objects.all().delete()
Convocation.objects.all().delete()
EpreuveExamen.objects.all().delete()
Examen.objects.all().delete()
Presence.objects.all().delete()
Creneau.objects.all().delete()
Note.objects.all().delete()
ValidationUE.objects.all().delete()
AffectationUE.objects.all().delete()
UniteEnseignement.objects.all().delete()
Inscription.objects.all().delete()
Etudiant.objects.all().delete()
Enseignant.objects.all().delete()
Paiement.objects.all().delete()
Bourse.objects.all().delete()
TypeFrais.objects.all().delete()
CommandeCantine.objects.all().delete()
RechargeCantine.objects.all().delete()
CantineCompte.objects.all().delete()
MenuJour.objects.all().delete()
PlatCantine.objects.all().delete()
PretOuvrage.objects.all().delete()
Bibliographie.objects.all().delete()
Semestre.objects.all().delete()
AnneeAcademique.objects.all().delete()
Filiere.objects.all().delete()
Departement.objects.all().delete()
Salle.objects.all().delete()
Faculte.objects.all().delete()
User.objects.filter(username__startswith='etu').delete()
User.objects.filter(username='directeuruni').delete()

# --- Paramètres ---
p = UniversiteParametre.obtenir()
p.nom_universite = 'UNIVERSITÉ COULSOFT'
p.sigle = 'UC'
p.slogan = 'Savoir, Innovation, Excellence'
p.recteur = 'Pr Sery Coulibaly'
p.adresse = 'Abidjan, Cocody — Boulevard de l\'Université'
p.telephone = '+225 00 00 00 00'
p.email = 'contact@univ.edu'
p.site_web = 'www.univ.edu'
p.devise = 'F CFA'
p.devise_code = 'FCFA'
p.note_maximale = Decimal('20.00')
p.seuil_validation = Decimal('10.00')
p.credit_annee = 60
p.mention_bulletin = 'Le présent relevé est délivré au titre du système LMD.'
p.save()

# --- Année académique ---
annee = AnneeAcademique.objects.create(
    libelle='2025-2026', date_debut=date(2025, 9, 8), date_fin=date(2026, 7, 10), active=True)

# --- Semestres (Licence : S1→S6) ---
semestres = {}
for i, (t, d1, d2) in enumerate([
    ('S1', '2025-09-08', '2026-01-09'), ('S2', '2026-01-12', '2026-05-29'),
    ('S3', '2025-09-08', '2026-01-09'), ('S4', '2026-01-12', '2026-05-29'),
    ('S5', '2025-09-08', '2026-01-09'), ('S6', '2026-01-12', '2026-05-29'),
]):
    y1, m1, j1 = map(int, d1.split('-'))
    y2, m2, j2 = map(int, d2.split('-'))
    semestres[t] = Semestre.objects.create(
        annee=annee, type=t, nom=f'Semestre {t}', date_debut=date(y1, m1, j1), date_fin=date(y2, m2, j2))

# --- Salles ---
salles = {}
for nom, typ, cap in [('Amphi A', 'amphi', 300), ('Amphi B', 'amphi', 250),
                      ('Salle 101', 'cours', 80), ('Salle 102', 'td', 60),
                      ('Labo Physique', 'tp', 40), ('Labo Chimie', 'tp', 40),
                      ('Salle Info 1', 'informatique', 45)]:
    salles[nom] = Salle.objects.create(nom=nom, type=typ, capacite=cap)

# --- Facultés, départements, filières ---
st = Faculte.objects.create(nom='Sciences et Technologies', code='ST', doyen='Pr Aya Kouassi',
                            description='Informatique, mathématiques et sciences de l\'ingénieur.')
sante = Faculte.objects.create(nom='Sciences de la Santé', code='SS', doyen='Pr Fatou Diarra',
                               description='Biologie et sciences biomédicales.')
seg = Faculte.objects.create(nom='Sciences Économiques et de Gestion', code='SEG',
                             doyen='Pr Moussa Bamba', description='Économie, gestion et commerce.')

dept_info = Departement.objects.create(faculte=st, nom='Informatique', code='INFO', chef='Dr Yao N\'Guessan')
dept_maths = Departement.objects.create(faculte=st, nom='Mathématiques', code='MATH', chef='Dr Koffi Adou')
dept_bio = Departement.objects.create(faculte=sante, nom='Biologie', code='BIO', chef='Dr Awa Camara')
dept_eco = Departement.objects.create(faculte=seg, nom='Économie', code='ECO', chef='Dr Ibrahim Soro')

filieres = {}
filieres['informatique'] = Filiere.objects.create(departement=dept_info, nom='Informatique', code='INF',
                                                  niveau='Licence', duree_annees=3,
                                                  description='Informatique générale, algorithmique et développement.')
filieres['mathematiques'] = Filiere.objects.create(departement=dept_maths, nom='Mathématiques', code='MATH',
                                                   niveau='Licence', duree_annees=3)
filieres['biologie'] = Filiere.objects.create(departement=dept_bio, nom='Biologie', code='BIO',
                                              niveau='Licence', duree_annees=3)
filieres['economie'] = Filiere.objects.create(departement=dept_eco, nom='Économie', code='ECO',
                                              niveau='Licence', duree_annees=3)

# --- Enseignants ---
enseignants = []
for nom, prenom, sexe, grade, dept, spec in [
    ('Kouassi', 'Jean', 'M', 'Maître-assistant', dept_info, 'Algorithmique & Base de données'),
    ('N\'Guessan', 'Aya', 'F', 'Maître de conférences', dept_info, 'Réseaux & Systèmes distribués'),
    ('Adou', 'Koffi', 'M', 'Assistant', dept_maths, 'Analyse & Probabilités'),
    ('Camara', 'Awa', 'F', 'Maître-assistant', dept_bio, 'Biologie cellulaire'),
    ('Soro', 'Ibrahim', 'M', 'Maître-assistant', dept_eco, 'Microéconomie'),
    ('Touré', 'Mariam', 'F', 'Chargé de cours', dept_bio, 'Chimie analytique'),
]:
    enseignants.append(Enseignant.objects.create(
        nom=nom, prenom=prenom, sexe=sexe, grade=grade, departement=dept, specialite=spec,
        telephone=f'+225 07 {len(enseignants) + 10} {len(enseignants) + 20} {len(enseignants) + 30}',
        email=f'{nom.lower()}.{prenom.lower()}@univ.edu', salaire_base=Decimal('450000'),
        charge_horaire=320))

# --- UE par filière ---
ues = {}
ue_spec = {
    'informatique': [
        ('INF111', 'Algorithmique et programmation I', 'fondamentale', 'S1', 6, 4),
        ('INF112', 'Architecture des ordinateurs', 'fondamentale', 'S1', 4, 3),
        ('INF113', 'Mathématiques discrètes', 'fondamentale', 'S1', 4, 3),
        ('INF114', 'Techniques d\'expression', 'transversale', 'S1', 2, 2),
        ('INF121', 'Programmation orientée objet', 'fondamentale', 'S2', 6, 4),
        ('INF122', 'Base de données', 'fondamentale', 'S2', 5, 3),
        ('INF123', 'Systèmes d\'exploitation', 'majeure', 'S2', 5, 3),
        ('INF124', 'Anglais scientifique', 'transversale', 'S2', 2, 2),
        ('INF131', 'Réseaux informatiques', 'majeure', 'S3', 6, 4),
        ('INF132', 'Génie logiciel', 'majeure', 'S3', 5, 3),
        ('INF133', 'Structures de données', 'fondamentale', 'S3', 5, 3),
        ('INF211', 'Développement web', 'professionnelle', 'S4', 6, 4),
        ('INF212', 'Intelligence artificielle', 'optionnelle', 'S4', 4, 3),
        ('INF311', 'Projet de fin d\'études', 'professionnelle', 'S6', 12, 5),
    ],
    'mathematiques': [
        ('MAT111', 'Analyse I', 'fondamentale', 'S1', 6, 4),
        ('MAT112', 'Algèbre linéaire', 'fondamentale', 'S1', 6, 4),
        ('MAT121', 'Analyse II', 'fondamentale', 'S2', 6, 4),
        ('MAT122', 'Probabilités', 'fondamentale', 'S2', 5, 3),
        ('MAT131', 'Analyse numérique', 'majeure', 'S3', 6, 4),
        ('MAT132', 'Statistiques', 'majeure', 'S3', 5, 3),
    ],
    'biologie': [
        ('BIO111', 'Biologie cellulaire', 'fondamentale', 'S1', 6, 4),
        ('BIO112', 'Chimie générale', 'fondamentale', 'S1', 4, 3),
        ('BIO113', 'Botanique', 'fondamentale', 'S1', 4, 3),
        ('BIO121', 'Génétique', 'fondamentale', 'S2', 6, 4),
        ('BIO122', 'Chimie organique', 'fondamentale', 'S2', 5, 3),
        ('BIO123', 'Zoologie', 'fondamentale', 'S2', 5, 3),
        ('BIO131', 'Microbiologie', 'majeure', 'S3', 6, 4),
        ('BIO132', 'Biochimie', 'majeure', 'S3', 5, 3),
    ],
    'economie': [
        ('ECO111', 'Microéconomie', 'fondamentale', 'S1', 6, 4),
        ('ECO112', 'Comptabilité générale', 'fondamentale', 'S1', 5, 3),
        ('ECO113', 'Mathématiques financières', 'fondamentale', 'S1', 4, 3),
        ('ECO121', 'Macroéconomie', 'fondamentale', 'S2', 6, 4),
        ('ECO122', 'Statistiques descriptives', 'fondamentale', 'S2', 5, 3),
        ('ECO123', 'Droit des affaires', 'transversale', 'S2', 4, 2),
        ('ECO131', 'Économie monétaire', 'majeure', 'S3', 6, 4),
        ('ECO132', 'Gestion financière', 'majeure', 'S3', 5, 3),
    ],
}
for filiere_cle, liste in ue_spec.items():
    fil = filieres[filiere_cle]
    for code, nom, typ, sem, cred, coef in liste:
        u = UniteEnseignement.objects.create(
            code=code, nom=nom, filiere=fil, semestre=semestres[sem],
            credits=cred, coefficient=Decimal(coef), type=typ,
            volume_horaire=cred * 5,
            description=f'{nom} — crédits ECTS : {cred}.')
        ues[code] = u

# --- Affectations UE ↔ enseignants ---
affectations = [
    ('INF111', 0), ('INF112', 1), ('INF113', 2), ('INF121', 0), ('INF122', 0),
    ('INF123', 1), ('INF131', 1), ('INF132', 0), ('INF133', 2),
    ('BIO111', 3), ('BIO112', 5), ('BIO121', 3), ('BIO131', 3), ('BIO132', 5),
    ('ECO111', 4), ('ECO121', 4), ('ECO131', 4), ('ECO132', 4),
    ('MAT111', 2), ('MAT112', 2), ('MAT121', 2), ('MAT122', 2),
]
for code, idx in affectations:
    AffectationUE.objects.create(ue=ues[code], enseignant=enseignants[idx],
                                 heures_cours=15, heures_td=10, heures_tp=5)

# --- Étudiants, comptes utilisateurs, inscriptions, cantine ---
donnees_etudiants = [
    ('Kouassi', 'Aminata', 'F', 'informatique', 1, True),
    ('Traoré', 'Sékou', 'M', 'informatique', 1, False),
    ('Diabaté', 'Mariam', 'F', 'informatique', 1, True),
    ('Koné', 'Adama', 'M', 'informatique', 2, False),
    ('Yao', 'Estelle', 'F', 'informatique', 2, True),
    ('Bamba', 'Ibrahima', 'M', 'mathematiques', 1, False),
    ('Cissé', 'Ramata', 'F', 'mathematiques', 1, True),
    ('Ouattara', 'Souleymane', 'M', 'mathematiques', 2, False),
    ('Camara', 'Fatim', 'F', 'biologie', 1, True),
    ('Soro', 'Yacouba', 'M', 'biologie', 1, False),
    ('N\'Guessan', 'Clarisse', 'F', 'economie', 1, True),
    ('Konaté', 'Lamine', 'M', 'economie', 1, False),
]
etudiants = []
for i, (nom, prenom, sexe, fil_cle, niveau, boursier) in enumerate(donnees_etudiants, start=1):
    etu = Etudiant.objects.create(
        nom=nom, prenom=prenom, sexe=sexe, date_naissance=date(2005, i % 12 + 1, i % 27 + 1),
        lieu_naissance='Abidjan', nationalite='Ivoirienne',
        adresse='Cocody, Abidjan', telephone=f'+225 07 00 {i:02d} 00',
        email=f'{nom.lower()}.{prenom.lower()}@etu.univ.edu',
        statut='actif', boursier=boursier, date_inscription=date(2025, 9, 8))
    if i <= 4:
        user = User.objects.create_user(f'etu{i}', email=etu.email, first_name=prenom, last_name=nom,
                                        password='etudiant123')
        etu.user = user
        etu.save(update_fields=['user'])
    Inscription.objects.create(
        etudiant=etu, annee=annee, filiere=filieres[fil_cle],
        niveau_annee=niveau, date=date(2025, 9, 8), statut='active',
        montant_paye=Decimal('150000'))
    if boursier:
        Bourse.objects.create(etudiant=etu, type='etat', montant_mensuel=Decimal('40000'),
                              date_debut=date(2025, 10, 1), date_fin=date(2026, 7, 31))
    etudiants.append(etu)

# --- Types de frais & paiements ---
frais_inscription = TypeFrais.objects.create(nom='Droits d\'inscription', montant=Decimal('150000'),
                                             periodicite='annuel', obligatoire=True)
frais_scolarite = TypeFrais.objects.create(nom='Scolarité annuelle', montant=Decimal('300000'),
                                           periodicite='annuel', obligatoire=True)
frais_labo = TypeFrais.objects.create(nom='Frais de laboratoire', montant=Decimal('25000'),
                                      periodicite='annuel', obligatoire=False)
frais_cantine = TypeFrais.objects.create(nom='Abonnement cantine', montant=Decimal('50000'),
                                         periodicite='annuel', obligatoire=False)

directeur = User.objects.create_user('directeuruni', 'directeur@univ.edu', password='admin123',
                                     first_name='Directeur', last_name='Université')
directeur.groups.add(Group.objects.get_or_create(name='Gestionnaire universitaire')[0])

for i, etu in enumerate(etudiants):
    Paiement.objects.create(etudiant=etu, annee=annee, type_frais=frais_inscription,
                            montant=Decimal('150000'), date=date(2025, 9, i % 20 + 5), mode='Especes',
                            enregistre_par=directeur)
    if i % 2 == 0:
        Paiement.objects.create(etudiant=etu, annee=annee, type_frais=frais_scolarite,
                                montant=Decimal('150000'), date=date(2025, 10, i % 25 + 1),
                                mode='Mobile Money', enregistre_par=directeur)

# --- Cantine : plats, menus, comptes, recharges, commandes ---
plats = {}
for nom, cat, prix, kcal, veg in [
    ('Riz gras poulet', 'plat', 1200, 650, False), ('Attiéké poisson', 'plat', 1000, 480, False),
    ('Sauce arachide', 'accompagnement', 600, 380, True), ('Bananes plantains', 'accompagnement', 400, 220, True),
    ('Fruit frais', 'dessert', 500, 90, True), ('Eau minérale', 'boisson', 300, 0, True),
    ('Café au lait', 'boisson', 500, 120, True), ('Poulet braisé', 'plat', 1800, 720, False),
]:
    plats[nom] = PlatCantine.objects.create(nom=nom, categorie=cat, prix=Decimal(prix),
                                            calories=kcal, vegetarien=veg)
aujourdhui = timezone.now().date()
MenuJour.objects.create(date=aujourdhui, type='dejeuner', plat=plats['Riz gras poulet'])
MenuJour.objects.create(date=aujourdhui, type='dejeuner', plat=plats['Attiéké poisson'])
MenuJour.objects.create(date=aujourdhui, type='dejeuner', plat=plats['Sauce arachide'])
MenuJour.objects.create(date=aujourdhui, type='dejeuner', plat=plats['Fruit frais'])
MenuJour.objects.create(date=aujourdhui, type='petit_dejeuner', plat=plats['Café au lait'])

comptes = []
for etu in etudiants:
    cpt = CantineCompte.objects.create(etudiant=etu, solde=Decimal('5000'))
    RechargeCantine.objects.create(compte=cpt, montant=Decimal('5000'), mode='Especes', enregistre_par=directeur)
    if etudiants.index(etu) % 3 == 0:
        RechargeCantine.objects.create(compte=cpt, montant=Decimal('10000'), mode='Mobile Money', enregistre_par=directeur)
    comptes.append(cpt)

for cpt in comptes[:8]:
    CommandeCantine.objects.create(compte=cpt, plat=plats['Riz gras poulet'], montant=Decimal('1200'))

# --- Notes (Informatique, L1) ---
etudiants_info = [e for e in etudiants if e.filiere == filieres['informatique'] and e.inscriptions.first().niveau_annee == 1]
ues_s1_info = [ues['INF111'], ues['INF112'], ues['INF113'], ues['INF114']]
ues_s2_info = [ues['INF121'], ues['INF122'], ues['INF123']]
valeurs_notes = {
    'INF111': (12, 14, 10, 15), 'INF112': (11, 9, 13, 12), 'INF113': (14, 12, 11, 13),
    'INF114': (15, 16, 13, 14), 'INF121': (10, 13, 12, 11), 'INF122': (13, 11, 15, 14),
    'INF123': (9, 12, 10, 13),
}
for i, etu in enumerate(etudiants_info):
    for ue in ues_s1_info + ues_s2_info:
        Note.objects.create(etudiant=etu, ue=ue, type='CC', note=Decimal(valeurs_notes[ue.code][i] + 1),
                            date=date(2025, 12, 10))
        Note.objects.create(etudiant=etu, ue=ue, type='EX', note=Decimal(valeurs_notes[ue.code][i]),
                            date=date(2026, 1, 10))
    for ue in ues_s1_info:
        ValidationUE.objects.create(etudiant=etu, ue=ue, semestre=semestres['S1'],
                                    moyenne=Decimal('12.50'), decision='valide')

# --- Présences (séance du jour sur INF111) ---
if ues_s1_info:
    for etu in etudiants_info:
        Presence.objects.create(etudiant=etu, ue=ues_s1_info[0], date=aujourdhui,
                                statut='Present' if etudiants_info.index(etu) % 4 else 'Absent')

# --- Emploi du temps ---
creneaux = [
    ('INF111', 'Lundi', '08:00', '10:00', 'Amphi A', 'CC'),
    ('INF111', 'Mercredi', '08:00', '10:00', 'Salle 101', 'TP'),
    ('INF122', 'Mardi', '10:00', '12:00', 'Salle Info 1', 'TP'),
    ('INF121', 'Jeudi', '08:00', '10:00', 'Salle 101', 'CC'),
    ('BIO111', 'Lundi', '14:00', '16:00', 'Labo Physique', 'TP'),
    ('ECO111', 'Mardi', '14:00', '16:00', 'Amphi B', 'CC'),
]
for code, jour, hd, hf, salle, typ in creneaux:
    if code in ues:
        h1, m1 = map(int, hd.split(':'))
        h2, m2 = map(int, hf.split(':'))
        Creneau.objects.create(ue=ues[code], jour=jour, heure_debut=time(h1, m1), heure_fin=time(h2, m2),
                               salle=salles[salle], type=typ)

# --- Examens ---
examen = Examen.objects.create(nom='Examen de fin de semestre S1', annee=annee, session='Normale',
                               date_debut=date(2026, 1, 19), date_fin=date(2026, 1, 30),
                               description='Session normale du premier semestre.')
epreuve = EpreuveExamen.objects.create(examen=examen, ue=ues['INF111'], date=date(2026, 1, 20),
                                       heure_debut=time(9, 0), duree=120, salle=salles['Amphi A'])
epreuve.surveillants.add(enseignants[0])
for etu in etudiants_info:
    Convocation.objects.create(epreuve=epreuve, etudiant=etu, present=True,
                               note_epreuve=Decimal(valeurs_notes['INF111'][etudiants_info.index(etu)]))

# --- Bibliothèque ---
ouvrages = [
    ('Algorithmique et programmation', 'Kouassi Jean', 'informatique', 'B-01', 2023, 5),
    ('Introduction aux bases de données', 'N\'Guessan Aya', 'informatique', 'B-02', 2022, 3),
    ('Analyse mathématique I', 'Adou Koffi', 'mathematiques', 'M-01', 2021, 4),
    ('Biologie cellulaire', 'Camara Awa', 'medecine', 'S-01', 2024, 3),
    ('Microéconomie moderne', 'Soro Ibrahim', 'economie', 'E-01', 2020, 4),
    ('Le LMD en Afrique', 'Collectif', 'litterature', 'L-01', 2019, 2),
]
livres = []
for titre, auteur, domaine, emplacement, annee_ed, quantite in ouvrages:
    livres.append(Bibliographie.objects.create(titre=titre, auteur=auteur, domaine=domaine,
                                               emplacement=emplacement, annee_edition=annee_ed, quantite=quantite))
PretOuvrage.objects.create(ouvrage=livres[0], etudiant=etudiants[0],
                           date_pret=date(2026, 6, 1), date_retour_prevue=date(2026, 7, 15))
PretOuvrage.objects.create(ouvrage=livres[1], etudiant=etudiants[1],
                           date_pret=date(2026, 6, 10), date_retour_prevue=date(2026, 7, 1))

# --- Laboratoire virtuel : 16 expériences (slugs branchés sur le moteur JS) ---
experiences = [
    dict(titre='Pendule simple', slug='pendule', discipline='physique', niveau='L1', difficulte=1, duree_minutes=15,
         objectif='Étudier le mouvement périodique d\'un pendule et vérifier la relation entre la longueur L et la période T.',
         protocole='1. Régler la longueur, l\'angle initial et la masse.\n2. Activer ou non les frottements.\n3. Lancer la simulation et observer le mouvement.\n4. Capturer des couples (L, T) pour plusieurs longueurs.\n5. Tracer T² en fonction de L et en déduire g.',
         consignes='Ne pas dépasser un angle initial de 30° pour rester dans l\'approximation des petites oscillations.',
         pictogrammes='port_obligatoire',
         materiel='Support de fixation\nFil inextensible\nMasse suspendue\nChronomètre\nRapporteur\nRègle graduée',
         notions='Période et fréquence\nPetites oscillations\nÉnergie mécanique du pendule\nRégression linéaire (T² = (4π²/g).L)',
         formule='T = 2π √(L/g)  ⟶  T² = (4π²/g) × L',
         competences='Mesurer une période\nVérifier une loi physique\nLinéariser et exploiter une droite'),
    dict(titre='Tir projectile', slug='projectile', discipline='physique', niveau='L1', difficulte=2, duree_minutes=20,
         objectif='Étudier la trajectoire d\'un projectile : portée, altitude maximale et influence de l\'angle de tir.',
         protocole='1. Régler la vitesse initiale, l\'angle et la hauteur de départ.\n2. Lancer et suivre la trajectoire.\n3. Capturer (angle, portée) pour différents angles à v₀ constante.\n4. Tracer la portée en fonction de sin(2θ) et vérifier R = v₀².sin(2θ)/g.',
         consignes='Portée maximale théorique pour un tir au sol : angle de 45°.',
         pictogrammes='port_obligatoire',
         materiel='Lanceur balistique\nBille\nPapier carbone\nMètre ruban\nRapporteur',
         notions='Composition des mouvements\nParabole de sûreté\nPortée et flèche\nFonction sin(2θ)',
         formule='R = (v₀² sin 2θ)/g ;  z_max = h₀ + (v₀² sin²θ)/(2g)',
         competences='Modéliser un mouvement de chute parabolique\nExploiter R = f(sin 2θ)\nEstimer une incertitude'),
    dict(titre='Chute libre', slug='chute-libre', discipline='physique', niveau='L1', difficulte=1, duree_minutes=12,
         objectif='Analyser la chute d\'un corps avec ou sans résistance de l\'air et vérifier la loi de Galilée.',
         protocole='1. Choisir la hauteur et la masse.\n2. Activer ou non la résistance de l\'air.\n3. Lancer et observer le mouvement.\n4. Relever le temps de chute pour plusieurs hauteurs.\n5. Tracer t² = f(h) et en déduire g.',
         consignes='Sans résistance de l\'air, le temps de chute ne dépend pas de la masse.',
         pictogrammes='port_obligatoire',
         materiel='Tube à vide\nCorps de masses différentes\nChronomètre à déclenchement automatique\nRègle de 1 m',
         notions='Champ de pesanteur\nAccélération constante\nVitesse limite\nÉnergie cinétique et potentielle',
         formule='h = ½ g t² ;  v = g t ;  v = √(2gh)',
         competences='Vérifier l\'indépendance de la masse\nTracer t² = f(h)\nDiscuter du rôle de la résistance de l\'air'),
    dict(titre='Ressort (oscillateur harmonique)', slug='ressort', discipline='physique', niveau='L1', difficulte=1, duree_minutes=15,
         objectif='Étudier les oscillations d\'un système masse-ressort et la pulsation propre ω = √(k/m).',
         protocole='1. Régler la raideur k, la masse m et l\'amplitude.\n2. Lancer la simulation.\n3. Capturer (masse, période T) pour plusieurs masses.\n4. Tracer T² = f(m) et en déduire k.',
         consignes='La période dépend de la masse et de la raideur, pas de l\'amplitude (faibles amplitudes).',
         pictogrammes='port_obligatoire',
         materiel='Ressort de raideur connue\nMasses marquées\nPotence\nChronomètre\nBalance',
         notions='Oscillateur harmonique\nPulsation propre\nConservation de l\'énergie\nPériode du ressort',
         formule='T = 2π √(m/k)  ⟶  T² = (4π²/k) × m',
         competences='Identifier un mouvement périodique\nVérifier T = 2π√(m/k)\nDéduire k par régression'),
    dict(titre='Loi d\'Ohm', slug='loi-ohm', discipline='physique', niveau='L2', difficulte=2, duree_minutes=20,
         objectif='Vérifier expérimentalement la loi d\'Ohm U = R.I dans un circuit série et déterminer une résistance.',
         protocole='1. Régler la tension délivrée par le générateur.\n2. Régler la résistance de la charge.\n3. Lire le courant et la tension aux bornes du conducteur.\n4. Capturer plusieurs couples (U, I).\n5. Tracer I = f(U), la pente donne 1/R.',
         consignes='Ne pas court-circuiter le générateur ; tension limitée à 20 V. Risque électrique : couper avant toute manipulation.',
         pictogrammes='electrique,port_obligatoire',
         materiel='Générateur de tension réglable\nRhéostat / résistances\nVoltmètre\nAmpèremètre\nFils de connexion',
         notions='Courant et tension\nRésistance et conductivité\nMontage série\nDroite caractéristique',
         formule='U = R × I  ⟶  I = (1/R) × U',
         competences='Câbler un circuit\nLire des appareils de mesure\nDéduire R d\'une régression'),
    dict(titre='Réfraction de la lumière (loi de Snell-Descartes)', slug='refraction', discipline='physique', niveau='L2', difficulte=2, duree_minutes=20,
         objectif='Vérifier la loi de Snell-Descartes n₁ sin i = n₂ sin r et déterminer l\'indice de réfraction d\'un milieu.',
         protocole='1. Choisir l\'angle d\'incidence et l\'indice du second milieu.\n2. Observer la déviation du rayon.\n3. Capturer des couples (i, r) pour plusieurs angles.\n4. Tracer sin(r) = f(sin(i)) ; la pente vaut n₁/n₂.',
         consignes='Ne jamais viser l\'œil avec un faisceau laser ; se protéger contre le rayonnement.',
         pictogrammes='rayonnement,port_obligatoire',
         materiel='Demi-cylindre en plexiglas\nSource lumineuse / laser\nRapporteur gradué\nFeuille blanche',
         notions='Indice de réfraction\nLoi de Snell-Descartes\nRéflexion et réfraction\nFonction sinus',
         formule='n₁ sin i = n₂ sin r',
         competences='Construire un rayon réfracté\nVérifier la loi de Snell-Descartes\nDéduire un indice par régression'),
    dict(titre='Gaz parfaits (loi de Mariotte)', slug='gaz-parfaits', discipline='physique', niveau='L2', difficulte=2, duree_minutes=20,
         objectif='Vérifier la loi des gaz parfaits PV = nRT à température constante (loi de Mariotte).',
         protocole='1. Régler la quantité de gaz et la température.\n2. Choisir le volume du cylindre.\n3. Lire la pression.\n4. Capturer des couples (V, P).\n5. Tracer P = f(1/V) : droite passant par l\'origine, pente nRT.',
         consignes='Vérifier l\'étanchéité du système ; manipuler les gaz avec précaution.',
         pictogrammes='port_obligatoire',
         materiel='Cylindre à piston étanche\nManomètre\nRègle graduée\nSource de chaleur contrôlée',
         notions='Pression, volume, température\nÉquation d\'état du gaz parfait\nIsotherme\nTransformation isotherme',
         formule='PV = nRT  ⟶  P = nRT × (1/V)',
         competences='Mesurer une pression\nTracer P = f(1/V)\nVérifier une loi d\'état'),
    dict(titre='Titrage acido-basique', slug='titration', discipline='chimie', niveau='L2', difficulte=2, duree_minutes=25,
         objectif='Réaliser un titrage virtuel d\'une solution acide par une base, suivre le pH et déterminer le volume équivalent.',
         protocole='1. Régler le volume de solution titrée et la concentration de la base.\n2. Activer l\'indicateur de fin de réaction.\n3. Verser la base et observer le changement de couleur.\n4. Capturer des couples (V, pH) autour de l\'équivalence.\n5. Repérer Véq sur la courbe pH = f(V) (dérivée maximale).',
         consignes='Porter des lunettes de protection et des gants ; ne jamais mélanger des produits sans consigne.',
         pictogrammes='corrosif,port_obligatoire',
         materiel='Burette graduée\nBécher\nSolution de soude (NaOH)\nSolution d\'acide chlorhydrique\npH-mètre\nAgitateur magnétique',
         notions='Réaction acide-base\nPoint d\'équivalence\nCourbe de titrage\nIndicateurs colorés',
         formule='HCl + NaOH → NaCl + H₂O ;  Véq = (Cₐ.Vₐ)/C_b',
         competences='Réaliser un titrage\nRepérer le saut de pH\nDéterminer une concentration inconnue'),
    dict(titre='Échelle de pH & indicateurs', slug='ph-indicateur', discipline='chimie', niveau='L1', difficulte=1, duree_minutes=15,
         objectif='Découvrir l\'échelle de pH, le changement de couleur des indicateurs et les notions d\'acide et de base.',
         protocole='1. Choisir le pH de la solution.\n2. Observer la couleur de l\'indicateur universel.\n3. Déterminer le caractère acide, neutre ou basique.\n4. Relier la couleur au domaine de virage.',
         consignes='Le papier pH ne se trempe qu\'une fois : ne pas re-tremper pour éviter la contamination.',
         pictogrammes='irritant,port_obligatoire',
         materiel='Indicateur universel\nPapier pH\nSolutions étalons\nBéchers\nThermomètre',
         notions='Échelle de pH\nAcide, base, neutralité\nConcentration en H₃O⁺ et OH⁻\nIndicateurs colorés',
         formule='pH = -log₁₀ [H₃O⁺] ;  pH + pOH = 14',
         competences='Interpréter l\'échelle de pH\nAssocier couleur et pH\nClasser acide/base'),
    dict(titre='Équation-bilan (combustion du propane)', slug='equation-bilan', discipline='chimie', niveau='L2', difficulte=1, duree_minutes=15,
         objectif='Équilibrer une équation-bilan et vérifier la conservation des atomes (loi de Lavoisier).',
         protocole='1. Observer la combustion du propane C₃H₈.\n2. Compter les atomes de chaque côté.\n3. Ajuster les coefficients pour équilibrer la réaction.\n4. Vérifier le bilan C, H, O et la masse totale.',
         consignes='Travailler dans un espace ventilé ; le dioxyde de carbone n\'est pas respirable.',
         pictogrammes='inflammable,port_obligatoire',
         materiel='Tableau périodique\nFiche réaction\nCalculatrice',
         notions='Conservation de la matière\nÉquation-bilan\nCoefficients stœchiométriques\nCombustion',
         formule='C₃H₈ + 5 O₂ → 3 CO₂ + 4 H₂O',
         competences='Équilibrer une équation\nVérifier un bilan atomique\nAppliquer la loi de Lavoisier'),
    dict(titre='Dilution & loi de Beer-Lambert', slug='dilution', discipline='chimie', niveau='L3', difficulte=2, duree_minutes=25,
         objectif='Préparer des solutions diluées, mesurer leur absorbance et vérifier la loi de Beer-Lambert A = ε.l.C.',
         protocole='1. Choisir la concentration de la solution mère et la longueur de cuve.\n2. Préparer les cuvettes par dilution (facteurs 1, 2, 4, 8, 16).\n3. Sélectionner une cuvette et capturer (C, A).\n4. Capturer les 5 points.\n5. Tracer A = f(C) : droite passant par l\'origine, pente ε.l.',
         consignes='Rincer les cuvettes entre deux mesures ; ne pas toucher les faces optiques.',
         pictogrammes='port_obligatoire',
         materiel='Spectrophotomètre\nCuvettes\nSolution mère colorée\nPipettes jaugées\nFioles jaugées 100 mL',
         notions='Concentration molaire\nFacteur de dilution\nAbsorbance et transmittance\nDosage spectrophotométrique',
         formule='A = ε.l.C',
         competences='Préparer une gamme de dilution\nÉtalonner un spectrophotomètre\nDoser par étalonnage'),
    dict(titre='Cinétique chimique (ordre 1)', slug='cinetique', discipline='chimie', niveau='L3', difficulte=3, duree_minutes=25,
         objectif='Suivre la concentration d\'un réactif au cours du temps et déterminer la constante de vitesse k d\'une réaction d\'ordre 1.',
         protocole='1. Régler la constante de vitesse k et la température.\n2. Choisir le temps de réaction.\n3. Lire [A] résiduel.\n4. Capturer des couples (t, [A]).\n5. Tracer ln[A] = f(t) : droite de pente -k.\n6. Observer l\'influence de la température (loi d\'Arrhenius).',
         consignes='Produits volatils et inflammables : travailler sous hotte, pas de flamme.',
         pictogrammes='inflammable,port_obligatoire',
         materiel='Ballon réacteur\nBain thermostaté\nSpectrophotomètre / conductimètre\nChronomètre\nThermomètre',
         notions='Vitesse de réaction\nOrdre de réaction\nTemps de demi-réaction\nLoi d\'Arrhenius',
         formule='[A] = [A]₀ e⁻ᵏᵗ  ⟶  ln[A] = ln[A]₀ - k.t',
         competences='Suivre une cinétique\nLinéariser ln[A] = f(t)\nDéterminer k et le temps de demi-réaction'),
    dict(titre='Photosynthèse (production d\'O₂)', slug='photosynthese', discipline='biologie', niveau='L1', difficulte=1, duree_minutes=20,
         objectif='Observer l\'influence de la lumière, du CO₂ et de la température sur la production d\'O₂ par les végétaux.',
         protocole='1. Régler l\'intensité lumineuse, la teneur en CO₂ et la température.\n2. Lancer la simulation.\n3. Relever le débit de production d\'oxygène.\n4. Capturer des couples (lumière, taux) et identifier la saturation.',
         consignes='La température optimale de photosynthèse se situe entre 25 et 30 °C.',
         pictogrammes='port_obligatoire',
         materiel='Élode du Canada\nEprouvette à gaz\nLampes\nThermomètre\nSolution de bicarbonate',
         notions='Photosynthèse et respiration\nFacteurs limitants\nSpectre d\'absorption\nÉnergie lumineuse',
         formule='6 CO₂ + 6 H₂O + lumière → C₆H₁₂O₆ + 6 O₂',
         competences='Expérimenter avec un facteur variable\nIdentifier un facteur limitant\nLire et interpréter un graphique'),
    dict(titre='Microscope optique (calibration)', slug='microscope', discipline='biologie', niveau='L1', difficulte=1, duree_minutes=15,
         objectif='Utiliser un microscope virtuel, calibrer le champ et estimer la taille d\'objets biologiques.',
         protocole='1. Choisir le grossissement.\n2. Faire la mise au point.\n3. Compter les cellules visibles dans le champ.\n4. Calculer le diamètre réel du champ (5000/G µm).\n5. Capturer (G, diamètre) et vérifier diamètre = f(1/G).',
         consignes='Utiliser l\'oculaire côté œil, régler l\'éclairage à intensité modérée.',
         pictogrammes='',
         materiel='Microscope optique\nLame et lamelle\nPréparation de cellules végétales\nMicromètre objet',
         notions='Grossissement et résolution\nChamp visuel\nÉchelle et calibration\nCellule végétale',
         formule='Diamètre du champ (µm) = 5000 / G',
         competences='Régler un microscope\nCalibrer le champ\nEstimer une taille cellulaire'),
    dict(titre='Électrophorèse sur gel d\'ADN', slug='electrophorese', discipline='biologie', niveau='M1', difficulte=2, duree_minutes=25,
         objectif='Réaliser une électrophorèse virtuelle, construire une courbe étalon et estimer la taille d\'un fragment d\'ADN.',
         protocole='1. Choisir la taille de l\'échantillon inconnu et la tension.\n2. Lancer la migration.\n3. Mesurer les distances des fragments marqueurs.\n4. Capturer (taille, distance).\n5. Tracer distance = f(log₁₀ M) : droite étalon négative.\n6. Interpoler la taille de l\'échantillon.',
         consignes='Tension élevée : ne pas ouvrir la cuve pendant la migration (risque électrique).',
         pictogrammes='electrique,biologique,port_obligatoire',
         materiel='Cuve à électrophorèse\nGel d\'agarose\nMarqueurs de taille\nÉchantillon d\'ADN\nSystème UV (sous contrôle)',
         notions='Charge et migration\nGel d\'agarose\nCourbe étalon\nTaille d\'un fragment',
         formule='d = a - b.log₁₀(M)  (migration inverse du log de la taille)',
         competences='Mesurer des distances sur un gel\nConstruire une courbe étalon\nInterpoler une taille d\'ADN'),
    dict(titre='Respiration cellulaire & loi d\'Arrhenius', slug='respiration', discipline='biologie', niveau='L2', difficulte=2, duree_minutes=20,
         objectif='Mesurer la consommation d\'oxygène d\'un organisme en fonction de la température et déterminer l\'énergie d\'activation de la respiration.',
         protocole='1. Régler la température du bain.\n2. Lancer la mesure sur 10 minutes.\n3. Lire le taux de consommation d\'O₂.\n4. Capturer (T, taux) pour plusieurs températures.\n5. Tracer ln(taux) = f(1/T) et en déduire Ea = -R × pente.',
         consignes='Bain thermostaté : attention aux brûlures ; manipuler l\'organisme avec douceur.',
         pictogrammes='biologique,port_obligatoire',
         materiel='Respiromètre\nBain thermostaté\nThermomètre\nGraines en germination\nSoude (absorption du CO₂)',
         notions='Respiration aérobie\nQuotient respiratoire\nLoi d\'Arrhenius\nRythme métabolique',
         formule='r = k₀ e^(-Ea/RT)  ⟶  ln r = ln k₀ - (Ea/R)(1/T)',
         competences='Mesurer une consommation de gaz\nÉtudier l\'effet de la température\nDéterminer une énergie d\'activation'),
]
for exp in experiences:
    ExperienceLabo.objects.create(**exp, actif=True)

print('Données de démonstration université créées.')
print('  → 3 facultés, 4 filières, 12 étudiants, UE LMD, notes, cantine, bibliothèque, labo (16 expériences).')
print('  → Accès administration : admin (ou directeuruni) / admin123')
print('  → Accès étudiant (laboratoire) : etu1 / etudiant123')
