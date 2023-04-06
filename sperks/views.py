from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from sorl.thumbnail import get_thumbnail

from core.utils import payment_required, require_filled_profile
from skigit_project import settings
from user.models import Profile
from user.serializers import api_request_images


@method_decorator(login_required(login_url='/'), name="dispatch")
@method_decorator(payment_required, name="dispatch")
@method_decorator(require_filled_profile, name="dispatch")
class Sperks(TemplateView):
    """ Comment: Sperk list display by business user who provide incentive
        Args: request: Request method
        Returns: Sperk (First Business Logo)
    """

    def get(self, request):
        template = 'sperk/sperk.html',
        page_template = 'sperk/sperk_body.html'
        sperk_logo_list = []
        sperk_logo = Profile.objects.filter(business_verified=True).order_by('company_title')

        # when the request is ajax, filter logon on base of search value
        if request.is_ajax():
            template = page_template
            searchVal = request.GET.get('search', '')
            sperk_logo = sperk_logo.filter(company_title__icontains=searchVal)

        for b_logo in sperk_logo:
            if b_logo.is_completed['status']:
                if b_logo.logo_img.filter(is_deleted=False).all():
                    # print('test')

                    b_logo.img_id = b_logo.logo_img.filter(is_deleted=False).all()[0]
                    b_logo.b_img = get_thumbnail(
                        b_logo.logo_img.filter(
                            is_deleted=False
                        ).all()[0].logo, '100x100', quality=99, format='PNG'
                    ).url
                    # b_logo.b_img = api_request_images(b_logo.logo_img.filter(is_deleted=False).all()[0].logo,
                    #                                  quality=99,
                    #                                  format='PNG')
                    sperk_logo_list.append(b_logo)

        context = {
            'page_template': page_template,
            'sperk_logo_list': sperk_logo_list,

        }

        return render(request, template, context)


@login_required(login_url='/')
def sperk_profile(request, user, logo):
    """
        On Click of Sperk logo page will be redirect to
        Sperk profile, page having information related
        Sperk

    Args:
        request: Requested Method GET POST
        user: user_id
        logo: sperk (Logo id)

    Returns:
        Sperk (Business Logo) detail view

    """

    if User.objects.filter(id=request.user.id).exists():
        ski_share_list = []
        busniess_logo = []
        friend_list = []
        like_dict = []
        id = user
        logoid = logo
        profile_list = Profile.objects.filter(user__id=user)
        try:
            request_user = User.objects.get(pk=profile_list[0].user.id, is_active=True)
        except ObjectDoesNotExist:
            messages.error(request, 'Sorry, Your Request User Not Found.')
            return HttpResponseRedirect('/')  # HttpResponseRedirect
        busniesslogo = BusinessLogo.objects.get(id=logo, is_deleted=False)

        for b_logo in profile_list:
            for bb_logo in b_logo.logo_img.filter(is_deleted=False).all():
                bb_logo.img_id = bb_logo.id
                # bb_logo.l_img = get_thumbnail(bb_logo.logo, '300x120', quality=99, format='PNG').url
                bb_logo.l_img = api_request_images(bb_logo.logo, quality=99, format='PNG')
                busniess_logo.append(bb_logo)

        for user_list in profile_list:
            company_url = ProfileUrl.objects.filter(user=user_list.user)

        if Embed.objects.filter(to_user=request_user, is_embed=True).exists():
            embed_skigit_list = Embed.objects.filter(to_user=request_user, is_embed=True).values_list(
                'skigit_id',
                flat=True)
            if request.user.is_authenticated:
                if Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id),
                                         status=1).exists():
                    f_list = Friend.objects.filter(Q(to_user=request.user.id) | Q(from_user=request.user.id),
                                                   status=1)
                    from_user_list = f_list.exclude(from_user=request.user.id).values_list('from_user',
                                                                                           flat=True).distinct()
                    to_user_list = f_list.exclude(to_user=request.user.id).values_list('to_user',
                                                                                       flat=True).distinct()
                    fr_list = list(merge(from_user_list, to_user_list))
                    friends_detail = Profile.objects.filter(user__id__in=fr_list).order_by('user__username')
                    for friends in friends_detail:
                        if friends.profile_img:
                            # l_img = get_thumbnail(friends.profile_img, '35x35', quality=99, format='PNG').url
                            l_img = api_request_images(friends.profile_img, quality=99, format='PNG')
                        else:
                            l_img = "{0}{1}".format(settings.STATIC_URL,'skigit/detube/images/noimage_user.jpg')
                        friend_list.append({'uid': friends.user.id, 'username': friends.user.username,
                                            'name': friends.user.get_full_name(), 'image': l_img})
                video_likes = Like.objects.filter(user_id=request.user.id, status=True)
                for likes in video_likes:
                    like_dict.append(likes.skigit_id)
            vid = VideoDetail.objects.select_related('skigit_id').filter(skigit_id__id__in=embed_skigit_list)
            serializer = VideoDetailSerializer(vid, many=True)
            for vid_data in vid:
                sharObj = Share.objects.filter(skigit_id=vid_data, is_active=True,
                                               user=profile_list[0].user).order_by(
                    'to_user', '-pk').distinct('to_user')
                for sh in sharObj:
                    ski_share_list.append(
                        {'share_date': sh.created_date, 'username': sh.to_user.username,
                         'vid': sh.skigit_id_id})
            request_user = request_user
            video_detail = serializer.data
            video_likes = like_dict
            friend_list = friend_list
            order_value = '1'
            togal_val = '1'
            skigit_list = ski_share_list
            users = get_all_logged_in_users()

    return render(request, 'sperk/sperk-profile.html', locals())
