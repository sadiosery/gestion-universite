from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='universite_dashboard'),
    path('inscription/', views.inscription_etudiant, name='universite_inscription_etudiant'),

    # Années & semestres
    path('annees/', views.annees, name='universite_annees'),
    path('annees/nouvelle/', views.annee_create, name='universite_annee_create'),
    path('annees/<int:pk>/modifier/', views.annee_update, name='universite_annee_update'),
    path('annees/<int:pk>/supprimer/', views.annee_delete, name='universite_annee_delete'),
    path('annees/<int:pk>/activer/', views.annee_activer, name='universite_annee_activer'),
    path('semestres/', views.semestres, name='universite_semestres'),
    path('semestres/nouveau/', views.semestre_create, name='universite_semestre_create'),
    path('semestres/<int:pk>/modifier/', views.semestre_update, name='universite_semestre_update'),
    path('semestres/<int:pk>/supprimer/', views.semestre_delete, name='universite_semestre_delete'),

    # Organisation
    path('facultes/', views.facultes, name='universite_facultes'),
    path('facultes/nouvelle/', views.faculte_create, name='universite_faculte_create'),
    path('facultes/<int:pk>/modifier/', views.faculte_update, name='universite_faculte_update'),
    path('facultes/<int:pk>/supprimer/', views.faculte_delete, name='universite_faculte_delete'),
    path('departements/', views.departements, name='universite_departements'),
    path('departements/nouveau/', views.departement_create, name='universite_departement_create'),
    path('departements/<int:pk>/modifier/', views.departement_update, name='universite_departement_update'),
    path('departements/<int:pk>/supprimer/', views.departement_delete, name='universite_departement_delete'),
    path('filieres/', views.filieres, name='universite_filieres'),
    path('filieres/nouvelle/', views.filiere_create, name='universite_filiere_create'),
    path('filieres/<int:pk>/', views.filiere_detail, name='universite_filiere_detail'),
    path('filieres/<int:pk>/modifier/', views.filiere_update, name='universite_filiere_update'),
    path('filieres/<int:pk>/supprimer/', views.filiere_delete, name='universite_filiere_delete'),
    path('salles/', views.salles, name='universite_salles'),
    path('salles/nouvelle/', views.salle_create, name='universite_salle_create'),
    path('salles/<int:pk>/modifier/', views.salle_update, name='universite_salle_update'),
    path('salles/<int:pk>/supprimer/', views.salle_delete, name='universite_salle_delete'),

    # Enseignants
    path('enseignants/', views.enseignants, name='universite_enseignants'),
    path('enseignants/nouveau/', views.enseignant_create, name='universite_enseignant_create'),
    path('enseignants/<int:pk>/modifier/', views.enseignant_update, name='universite_enseignant_update'),
    path('enseignants/<int:pk>/supprimer/', views.enseignant_delete, name='universite_enseignant_delete'),

    # Étudiants & inscriptions
    path('etudiants/', views.etudiants, name='universite_etudiants'),
    path('etudiants/nouveau/', views.etudiant_create, name='universite_etudiant_create'),
    path('etudiants/<int:pk>/', views.etudiant_detail, name='universite_etudiant_detail'),
    path('etudiants/<int:pk>/modifier/', views.etudiant_update, name='universite_etudiant_update'),
    path('etudiants/<int:pk>/supprimer/', views.etudiant_delete, name='universite_etudiant_delete'),
    path('export/etudiants/', views.export_etudiants, name='universite_export_etudiants'),
    path('inscriptions/', views.inscriptions, name='universite_inscriptions'),
    path('inscriptions/nouvelle/', views.inscription_create, name='universite_inscription_create'),
    path('inscriptions/<int:pk>/', views.inscription_detail, name='universite_inscription_detail'),

    # Pédagogie
    path('ues/', views.ues, name='universite_ues'),
    path('ues/nouvelle/', views.ue_create, name='universite_ue_create'),
    path('ues/<int:pk>/', views.ue_detail, name='universite_ue_detail'),
    path('ues/<int:pk>/modifier/', views.ue_update, name='universite_ue_update'),
    path('ues/<int:pk>/supprimer/', views.ue_delete, name='universite_ue_delete'),
    path('affectations/', views.affectations, name='universite_affectations'),
    path('affectations/nouvelle/', views.affectation_create, name='universite_affectation_create'),
    path('affectations/<int:pk>/modifier/', views.affectation_update, name='universite_affectation_update'),
    path('affectations/<int:pk>/supprimer/', views.affectation_delete, name='universite_affectation_delete'),
    path('cours/', views.cours_en_ligne, name='universite_cours'),
    path('cours/nouveau/', views.cours_en_ligne_create, name='universite_cours_create'),
    path('cours/<int:pk>/', views.cours_en_ligne_detail, name='universite_cours_detail'),
    path('cours/<int:pk>/modifier/', views.cours_en_ligne_update, name='universite_cours_update'),
    path('cours/<int:pk>/supprimer/', views.cours_en_ligne_delete, name='universite_cours_delete'),

    # Notes & relevés
    path('notes/', views.notes, name='universite_notes'),
    path('notes/saisie/', views.saisie_notes, name='universite_saisie_notes'),
    path('notes/supprimer/<int:pk>/', views.note_delete, name='universite_note_delete'),
    path('releves/', views.releves, name='universite_releves'),
    path('releves/etudiant/<int:pk>/', views.releve_etudiant, name='universite_releve_etudiant'),
    path('deliberation/', views.deliberer, name='universite_deliberer'),

    # Présences & emploi du temps
    path('presences/', views.presences, name='universite_presences'),
    path('presences/appel/', views.appel, name='universite_appel'),
    path('presences/supprimer/<int:pk>/', views.presence_delete, name='universite_presence_delete'),
    path('emplois/', views.emplois, name='universite_emplois'),
    path('emplois/nouveau/', views.emploi_create, name='universite_emploi_create'),
    path('emplois/supprimer/<int:pk>/', views.emploi_delete, name='universite_emploi_delete'),

    # Examens
    path('examens/', views.examens, name='universite_examens'),
    path('examens/nouveau/', views.examen_create, name='universite_examen_create'),
    path('examens/<int:pk>/', views.examen_detail, name='universite_examen_detail'),
    path('examens/<int:pk>/modifier/', views.examen_update, name='universite_examen_update'),
    path('examens/<int:pk>/supprimer/', views.examen_delete, name='universite_examen_delete'),
    path('examens/<int:examen_pk>/epreuve/', views.epreuve_create, name='universite_epreuve_create'),
    path('epreuves/<int:epreuve_pk>/convocation/', views.epreuve_convoquer, name='universite_epreuve_convoquer'),
    path('epreuves/<int:pk>/supprimer/', views.epreuve_delete, name='universite_epreuve_delete'),

    # Scolarité
    path('paiements/', views.paiements, name='universite_paiements'),
    path('paiements/nouveau/', views.paiement_create, name='universite_paiement_create'),
    path('paiements/<int:pk>/recu/', views.paiement_recu, name='universite_paiement_recu'),
    path('paiements/<int:pk>/supprimer/', views.paiement_delete, name='universite_paiement_delete'),
    path('paiements/impayes/', views.impayes, name='universite_impayes'),
    path('export/paiements/', views.export_paiements, name='universite_export_paiements'),
    path('frais/', views.types_frais, name='universite_types_frais'),
    path('frais/nouveau/', views.type_frais_create, name='universite_type_frais_create'),
    path('frais/<int:pk>/modifier/', views.type_frais_update, name='universite_type_frais_update'),
    path('frais/<int:pk>/supprimer/', views.type_frais_delete, name='universite_type_frais_delete'),
    path('bourses/', views.bourses, name='universite_bourses'),
    path('bourses/nouvelle/', views.bourse_create, name='universite_bourse_create'),

    # Cantine
    path('cantine/', views.cantine, name='universite_cantine'),
    path('cantine/service/', views.cantine_service, name='universite_cantine_service'),
    path('cantine/plats/', views.plats, name='universite_plats'),
    path('cantine/plats/nouveau/', views.plat_create, name='universite_plat_create'),
    path('cantine/plats/<int:pk>/modifier/', views.plat_update, name='universite_plat_update'),
    path('cantine/plats/<int:pk>/supprimer/', views.plat_delete, name='universite_plat_delete'),
    path('cantine/menus/', views.menus, name='universite_menus'),
    path('cantine/menus/nouveau/', views.menu_create, name='universite_menu_create'),
    path('cantine/menus/<int:pk>/modifier/', views.menu_update, name='universite_menu_update'),
    path('cantine/menus/supprimer/<int:pk>/', views.menu_delete, name='universite_menu_delete'),
    path('cantine/comptes/', views.comptes_cantine, name='universite_comptes'),
    path('cantine/comptes/nouveau/', views.compte_create, name='universite_compte_create'),
    path('cantine/comptes/<int:pk>/', views.compte_detail, name='universite_compte_detail'),
    path('cantine/comptes/<int:pk>/supprimer/', views.compte_delete, name='universite_compte_delete'),
    path('cantine/recharges/', views.recharges, name='universite_recharges'),
    path('cantine/recharges/nouvelle/', views.recharge_create, name='universite_recharge_create'),
    path('cantine/recharges/supprimer/<int:pk>/', views.recharge_delete, name='universite_recharge_delete'),
    path('cantine/commandes/', views.commandes_cantine, name='universite_commandes'),
    path('cantine/commandes/nouvelle/', views.commande_create, name='universite_commande_create'),
    path('cantine/commandes/annuler/<int:pk>/', views.commande_annuler, name='universite_commande_annuler'),

    # Laboratoire virtuel
    path('labo/', views.labo, name='universite_labo'),
    path('labo/<slug:slug>/', views.labo_experience, name='universite_labo_experience'),
    path('labo-rapports/', views.labo_rapports, name='universite_labo_rapports'),
    path('labo-rapports/<int:pk>/csv/', views.labo_rapport_csv, name='universite_labo_rapport_csv'),
    path('labo-references/', views.labo_references, name='universite_labo_references'),

    # Bibliothèque
    path('bibliotheque/', views.bibliotheque, name='universite_bibliotheque'),
    path('bibliotheque/livres/nouveau/', views.livre_create, name='universite_livre_create'),
    path('bibliotheque/prets/', views.prets, name='universite_prets'),
    path('bibliotheque/prets/nouveau/', views.pret_create, name='universite_pret_create'),
    path('bibliotheque/prets/retour/<int:pk>/', views.pret_retour, name='universite_pret_retour'),

    # Rapports & configuration
    path('rapports/', views.rapports, name='universite_rapports'),
    path('parametres/', views.parametres, name='universite_parametres'),
    path('utilisateurs/', views.utilisateurs, name='universite_utilisateurs'),
    path('utilisateurs/nouveau/', views.utilisateur_create, name='universite_utilisateur_create'),
    path('utilisateurs/<int:pk>/modifier/', views.utilisateur_update, name='universite_utilisateur_update'),
    path('utilisateurs/<int:pk>/activer/', views.utilisateur_activer, name='universite_utilisateur_activer'),
    path('utilisateurs/<int:pk>/supprimer/', views.utilisateur_delete, name='universite_utilisateur_delete'),

    # Sauvegardes
    path('sauvegarde/', views.sauvegarde, name='universite_sauvegarde'),
    path('sauvegarde/creer/', views.sauvegarde_creer, name='universite_sauvegarde_creer'),
    path('sauvegarde/<int:pk>/telecharger/', views.sauvegarde_telecharger, name='universite_sauvegarde_telecharger'),
    path('sauvegarde/<int:pk>/restaurer/', views.sauvegarde_restaurer, name='universite_sauvegarde_restaurer'),
    path('sauvegarde/<int:pk>/supprimer/', views.sauvegarde_supprimer, name='universite_sauvegarde_supprimer'),
]
