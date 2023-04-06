import asyncio, json
from django.contrib.auth import get_user_model
from channels.consumer import AsyncConsumer
from channels.db import database_sync_to_async

class UserConsumer(AsyncConsumer):
	async def websocket_connect(self, event):
		user_token = self.scope['url_route']['kwargs']['user_token']
		user = get_user_model().objects.filter(id=user_token)
		if user.exists():
			chat_room = "thread_{}".format(user_token)
			self.chat_room = chat_room
			await self.channel_layer.group_add(
				chat_room,
				self.channel_name
			)

		await self.send({
			"type": "websocket.accept",
		})


	async def websocket_receive(self, event):
		myResponse = {
			"message": msg,
			"username": username
		}
		new_event = {
			"type": "chat_message",
			"text": json.dumps(myResponse)
		}

		await self.channel_layer.group_send(
			self.chat_room,
			new_event
		)

	async def chat_message(self, event):
		await self.send({
			"type": "websocket.send",
			"text": event['text']
		})

	async def websocket_disconnect(self, event):
		print("disconnected", event)
