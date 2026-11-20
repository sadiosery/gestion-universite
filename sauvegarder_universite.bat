@echo off
rem Sauvegarde planifiee de la base UniversiteGest (a utiliser dans le Planificateur de taches Windows).
rem Exemple : action = C:\Users\SADIO SERY COULIBALY\Documents\Default Project\universiteprojet\sauvegarder_universite.bat
"C:\Program Files\Python313\python.exe" "C:\Users\SADIO SERY COULIBALY\Documents\Default Project\universiteprojet\manage.py" sauvegarde_bd --conserver 10 >> "C:\Users\SADIO SERY COULIBALY\Documents\Default Project\universiteprojet\sauvegardes\historique_bat.log" 2>&1
