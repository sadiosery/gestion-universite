from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def get_item(dictionnaire, cle):
    """Accès dictionnaire par clé variable : {{ dict|get_item:variable }}"""
    try:
        return dictionnaire.get(cle)
    except AttributeError:
        return None


@register.filter
def split(texte, separateur="\n"):
    """Découpe un texte en lignes : {% for l in texte|split %}"""
    if not texte:
        return []
    return [l for l in texte.split(separateur) if l.strip()]


@register.filter
def etoiles(difficulte):
    """Rend les étoiles de difficulté sous forme de chaîne sûr HTML."""
    try:
        n = int(difficulte)
    except (TypeError, ValueError):
        n = 0
    return mark_safe('★' * n)
