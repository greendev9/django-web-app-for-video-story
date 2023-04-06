from django.conf.urls import url
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from user.consumers import UserConsumer

application = ProtocolTypeRouter({
    # Empty for now (http->django views is added by default)
    'websocket':
		# AllowedHostsOriginValidator(
    	AuthMiddlewareStack(
    		URLRouter(
    			[
    				url(r"^notification/(?P<user_token>[\w.@+-]+)", UserConsumer),
    			]
    		)
    	)
    # )
})