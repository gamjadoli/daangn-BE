from ninja import Router

from django.shortcuts import render

router = Router()


@router.get("/privacy")
def eu_consent(request):
    return render(request, "legal/eu_consent.html")
