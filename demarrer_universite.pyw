"""Demarrage silencieux du serveur Django UniversiteGest (port 8001).

Lance via pythonw.exe (aucune fenetre console). Les sorties standard et
d'erreur sont redirigees vers des fichiers journaux dans le projet.
Usage : demarrer_universite.pyw [port]  (port par defaut : 8001)
"""
import io
import os
import sys

PROJET = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(PROJET, "serveur_universite.log")
ERR = os.path.join(PROJET, "serveur_universite.err")


def main():
    port = 8001
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except (TypeError, ValueError):
            port = 8001
    os.chdir(PROJET)
    sys.path.insert(0, PROJET)
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    try:
        sys.stdout = open(LOG, "a", encoding="utf-8", buffering=1)
        sys.stderr = open(ERR, "a", encoding="utf-8", buffering=1)
    except OSError:
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
    from django.core.management import execute_from_command_line

    execute_from_command_line(
        [sys.argv[0], "runserver", f"0.0.0.0:{port}", "--noreload"]
    )


if __name__ == "__main__":
    main()
