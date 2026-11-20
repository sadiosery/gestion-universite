"""Middleware de restriction de visibilité des pages par utilisateur."""

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import Resolver404, resolve

from .decorators import est_personnel
from .pages_catalogue import URL_PAGE


class VisibilitePageMiddleware:
    """Refuse l'accès aux pages non autorisées pour le personnel restreint.

    Le tableau de bord reste toujours accessible. Un utilisateur du personnel
    qui n'a aucune page configurée voit toutes les pages (rétrocompatibilité).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if (user and user.is_authenticated and not user.is_superuser
                and est_personnel(user)):
            codes = set(user.pages_visibles.values_list('code', flat=True))
            if codes:
                url_name = None
                try:
                    url_name = resolve(request.path_info).url_name
                except Resolver404:
                    pass
                code = URL_PAGE.get(url_name)
                if code and code != 'dashboard' and code not in codes:
                    messages.warning(
                        request,
                        'Accès refusé : cette page n\'est pas autorisée pour votre compte.')
                    return redirect('universite_dashboard')
        return self.get_response(request)
