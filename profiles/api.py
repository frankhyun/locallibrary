from ninja import Router

from .schemas import MeOut, ProfileIn, ProfileOut

router = Router(tags=["me"])


@router.get("/", response=MeOut)
def me(request):
    return request.auth


@router.put("/profile", response=ProfileOut)
def update_profile(request, payload: ProfileIn):
    profile = request.auth.profile
    profile.display_name = payload.display_name
    profile.bio = payload.bio
    profile.save(update_fields=["display_name", "bio"])
    return profile
