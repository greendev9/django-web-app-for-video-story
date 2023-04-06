import json
from django.http import QueryDict, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import render
from django.urls import resolve

from django.conf import settings
from core.utils import (mobile_deep_link_data)

class JSONMiddleware(MiddlewareMixin):
    """ Process application/json requests data from GET and POST requests.
    """

    def process_request(self, request):
        if request.META.get('CONTENT_TYPE') and 'application/json' in request.META['CONTENT_TYPE']:
            # load the json data
            data = json.loads(request.body)
            # for consistency sake, we want to return
            # a Django QueryDict and not a plain Dict.
            # The primary difference is that the QueryDict stores
            # every value in a list and is, by default, immutable.
            # The primary issue is making sure that list values are
            # properly inserted into the QueryDict.  If we simply
            # do a q_data.update(data), any list values will be wrapped
            # in another list. By iterating through the list and updating
            # for each value, we get the expected result of a single list.
            q_data = QueryDict('', mutable=True)
            for key, value in data.items():
                if isinstance(value, list):
                    # need to iterate through the list and upate
                    # so that the list does not get wrapped in an
                    # additional list.
                    for x in value:
                        q_data.update({key: x})
                else:
                    q_data.update({key: value})

            if request.method == 'GET':
                request.GET = q_data

            if request.method == 'POST':
                request.POST = q_data

        return None

class MobileLandingPageRedirectMiddleware(MiddlewareMixin):
    """
        Redirect the mobile LP if user views the site in mobile device!

        By pass the API requests.
    """

    # def process_request(self, request):
    def process_view(self, request, view_func, view_args, view_kwargs):
        url_path = request.build_absolute_uri('?')
        # print(request.GET)
        # print(request.user_agent.is_mobile)
        # print(request.user_agent)
        api_request = ('deviceToken' in request.POST or 'deviceType' in request.POST or
                       'deviceToken' in request.GET or 'deviceType' in request.GET or url_path.find('/api/v1/') >= 0)
        #if not api_request and not request.GET.get('category', '') == settings.DEEPLINK_CATEGORY and request.user_agent.is_mobile:
        if api_request or not request.user_agent.is_mobile:
            return None
        else:
            """
                Check url deep link mobile app
            """
            url_name = resolve(request.path_info).url_name

            # TOS links need to be opened in mobile app also
            if url_name in ['t_and_c_view', 'acceptable_use_policy_view', 'privacy_policy_view']:
                return None

            fallback_url = mobile_deep_link_data(request, url_name, view_kwargs)
            if url_name == 'user_payment_setup':
                template_name = 'mobile_landing_page_invoice.html'
                return render(request, template_name)
            # elif fallback_url is not None and len(fallback_url) > 0 and not url_name == 'index':

            #     template_name = 'mobile_universal_link.html'
            #     context = {
            #         "ios_app_id": settings.IOS_APP_STORE_ID,
            #         "ios_app_name": settings.IOS_APP_STORE_NAME,
            #         "ios_app_scheme": settings.IOS_APP_SCHEME,
            #         "ios_app_host": settings.IOS_APP_HOST,
            #         "ios_app_url": fallback_url[1],

            #         "android_app_package": settings.ANDROID_APP_PACKAGE,
            #         "android_app_scheme": settings.ANDROID_APP_SCHEME,
            #         "android_app_host": settings.ANDROID_APP_HOST,
            #         "android_app_url": fallback_url[0],
            #     }
            #     return render(request, template_name, context)
            elif request.path.find('/static/') >= 0 or request.path.find('/media/') >= 0:
                return None
            else:
                template_name = 'mobile_landing_page.html'
                context = {'mobile_api_request': True}
                return render(request, template_name, context)

