from ninja import Router

router = Router()


@router.get("/health")
def health_check(request):
    return {"status": "ok"}
