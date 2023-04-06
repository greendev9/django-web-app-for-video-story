import pytest

from user.models import ExtraProfileImage, ProfileImg, BusinessLogo, ProfileUrl, Profile


@pytest.mark.django_db
def test_extraProfileImage_model():
    extraProfileImage = ExtraProfileImage(profile_img="skigit/extraProfileImage",is_active=True
                        )
    extraProfileImage.save()

    assert extraProfileImage.profile_img == "skigit/extraProfileImage"
    assert extraProfileImage.is_active == True

@pytest.mark.django_db
def test_profileImg_model():
    profileImg = ProfileImg(profile_img="skigit/profileImg",is_active=True
                        )
    profileImg.save()

    assert profileImg.profile_img == "skigit/profileImg"
    assert profileImg.is_active == True

@pytest.mark.django_db
def test_businessLogo_model():
    businessLogo = BusinessLogo(logo="skigit/businessLogo",is_deleted=False
                        )
    businessLogo.save()

    assert businessLogo.logo == "skigit/businessLogo"
    assert businessLogo.is_deleted == False

