"""Catalogue des pages de l'application pour la restriction de visibilité.

Chaque page associe un code, un libellé, sa route principale et l'ensemble
des noms de routes (URL) qui en dépendent. Ce catalogue alimente à la fois
le formulaire de gestion des utilisateurs et le middleware qui refuse l'accès
aux pages non autorisées.
"""

PAGES = [
    # (code, titre, url_name, section, url_names rattachés)
    ('dashboard', 'Tableau de bord', 'universite_dashboard', 'Accueil',
     {'universite_dashboard'}),
    ('annees', 'Années académiques', 'universite_annees', 'Organisation',
     {'universite_annees', 'universite_annee_create', 'universite_annee_update',
      'universite_annee_delete', 'universite_annee_activer'}),
    ('semestres', 'Semestres', 'universite_semestres', 'Organisation',
     {'universite_semestres', 'universite_semestre_create',
      'universite_semestre_update', 'universite_semestre_delete'}),
    ('facultes', 'Facultés', 'universite_facultes', 'Organisation',
     {'universite_facultes', 'universite_faculte_create',
      'universite_faculte_update', 'universite_faculte_delete'}),
    ('departements', 'Départements', 'universite_departements', 'Organisation',
     {'universite_departements', 'universite_departement_create',
      'universite_departement_update', 'universite_departement_delete'}),
    ('filieres', 'Filières', 'universite_filieres', 'Organisation',
     {'universite_filieres', 'universite_filiere_create',
      'universite_filiere_detail', 'universite_filiere_update',
      'universite_filiere_delete'}),
    ('salles', 'Salles', 'universite_salles', 'Organisation',
     {'universite_salles', 'universite_salle_create',
      'universite_salle_update', 'universite_salle_delete'}),
    ('etudiants', 'Étudiants', 'universite_etudiants', 'Personnes',
     {'universite_etudiants', 'universite_etudiant_create',
      'universite_etudiant_detail', 'universite_etudiant_update',
      'universite_etudiant_delete', 'universite_export_etudiants'}),
    ('inscriptions', 'Inscriptions', 'universite_inscriptions', 'Personnes',
     {'universite_inscriptions', 'universite_inscription_create',
      'universite_inscription_detail'}),
    ('enseignants', 'Enseignants', 'universite_enseignants', 'Personnes',
     {'universite_enseignants', 'universite_enseignant_create',
      'universite_enseignant_update', 'universite_enseignant_delete'}),
    ('ues', 'Unités d\'enseignement', 'universite_ues', 'Pédagogie',
     {'universite_ues', 'universite_ue_create', 'universite_ue_detail',
      'universite_ue_update', 'universite_ue_delete'}),
    ('cours', 'Cours en ligne', 'universite_cours', 'Pédagogie',
     {'universite_cours', 'universite_cours_create', 'universite_cours_detail',
      'universite_cours_update', 'universite_cours_delete'}),
    ('affectations', 'Affectations d\'UE', 'universite_affectations', 'Pédagogie',
     {'universite_affectations', 'universite_affectation_create',
      'universite_affectation_update', 'universite_affectation_delete'}),
    ('emplois', 'Emploi du temps', 'universite_emplois', 'Pédagogie',
     {'universite_emplois', 'universite_emploi_create', 'universite_emploi_delete'}),
    ('notes', 'Notes & relevés', 'universite_notes', 'Pédagogie',
     {'universite_notes', 'universite_saisie_notes', 'universite_note_delete',
      'universite_releves', 'universite_releve_etudiant'}),
    ('deliberation', 'Délibération LMD', 'universite_deliberer', 'Pédagogie',
     {'universite_deliberer'}),
    ('presences', 'Présences', 'universite_presences', 'Pédagogie',
     {'universite_presences', 'universite_appel', 'universite_presence_delete'}),
    ('examens', 'Examens', 'universite_examens', 'Pédagogie',
     {'universite_examens', 'universite_examen_create', 'universite_examen_detail',
      'universite_examen_update', 'universite_examen_delete',
      'universite_epreuve_create', 'universite_epreuve_convoquer',
      'universite_epreuve_delete'}),
    ('paiements', 'Paiements', 'universite_paiements', 'Scolarité',
     {'universite_paiements', 'universite_paiement_create',
      'universite_paiement_recu', 'universite_paiement_delete',
      'universite_export_paiements'}),
    ('impayes', 'Impayés', 'universite_impayes', 'Scolarité',
     {'universite_impayes'}),
    ('frais', 'Types de frais', 'universite_types_frais', 'Scolarité',
     {'universite_types_frais', 'universite_type_frais_create',
      'universite_type_frais_update', 'universite_type_frais_delete'}),
    ('bourses', 'Bourses', 'universite_bourses', 'Scolarité',
     {'universite_bourses', 'universite_bourse_create'}),
    ('cantine', 'Cantine', 'universite_cantine', 'Services',
     {'universite_cantine', 'universite_plats', 'universite_plat_create',
      'universite_plat_update', 'universite_plat_delete', 'universite_menus',
      'universite_menu_create', 'universite_menu_update', 'universite_menu_delete',
      'universite_comptes', 'universite_compte_create', 'universite_compte_detail',
      'universite_compte_delete', 'universite_recharges',
      'universite_recharge_create', 'universite_recharge_delete',
      'universite_commandes', 'universite_commande_create',
      'universite_commande_annuler'}),
    ('labo', 'Laboratoire virtuel', 'universite_labo', 'Services',
     {'universite_labo', 'universite_labo_experience', 'universite_labo_rapports',
      'universite_labo_rapport_csv', 'universite_labo_references'}),
    ('bibliotheque', 'Bibliothèque', 'universite_bibliotheque', 'Services',
     {'universite_bibliotheque', 'universite_livre_create', 'universite_prets',
      'universite_pret_create', 'universite_pret_retour'}),
    ('rapports', 'Rapports & statistiques', 'universite_rapports', 'Administration',
     {'universite_rapports'}),
    ('parametres', 'Paramètres', 'universite_parametres', 'Administration',
     {'universite_parametres'}),
    ('utilisateurs', 'Utilisateurs & rôles', 'universite_utilisateurs', 'Administration',
     {'universite_utilisateurs', 'universite_utilisateur_create',
      'universite_utilisateur_update', 'universite_utilisateur_activer',
      'universite_utilisateur_delete'}),
    ('sauvegarde', 'Sauvegardes & restauration', 'universite_sauvegarde', 'Administration',
     {'universite_sauvegarde', 'universite_sauvegarde_creer',
      'universite_sauvegarde_telecharger', 'universite_sauvegarde_restaurer',
      'universite_sauvegarde_supprimer'}),
]

# Correspondance route (url_name) -> code de page
URL_PAGE = {}
for _code, _titre, _url, _section, _urls in PAGES:
    for _u in _urls:
        URL_PAGE[_u] = _code


def synchroniser_pages():
    """Crée les entrées manquantes du catalogue en base (get_or_create)."""
    from .models import Page
    for code, titre, url, section, _urls in PAGES:
        Page.objects.get_or_create(code=code, defaults={
            'titre': titre, 'url_name': url, 'section': section})


def codes_par_default():
    """Codes des pages cochées par défaut à la création d'un utilisateur."""
    return {code for code, *_ in PAGES if code != 'dashboard'}
