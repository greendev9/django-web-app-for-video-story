from swampdragon import route_handler
from swampdragon.route_handler import ModelPubRouter
from friends.serializers import NotificationSerializer
from friends.models import Notification


class NotificationRouter(ModelPubRouter):
    serializer_class = NotificationSerializer
    model = Notification
    route_name = 'notifications'
    valid_verbs = ['subscribe']

    def get_object(self, **kwargs):
        return self.model.objects.get(pk=kwargs['pk'])

    # @login_required(login_url='/')
    # def subscribe(self, **kwargs):
    #     super(self).subscribe(**kwargs)

    def get_query_set(self, **kwargs):
        return self.model.objects.all()

    def get_subscription_contexts(self, **kwargs):
        if self.connection.user:
            return {'user__id': self.connection.user.pk}

route_handler.register(NotificationRouter)
