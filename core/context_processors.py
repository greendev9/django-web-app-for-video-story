'''
Common context processor!
'''

from core.utils import is_user_business

def common_context(request):
    '''

    :param request:
    :return: Set the context variables throughout the site!
    '''

    context = {}
    if request.user.is_authenticated:
        context.update(is_business=is_user_business(request.user))
    return context