from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import async_to_sync
import json
from asgiref.sync import sync_to_async

class NotificationConsumer(AsyncWebsocketConsumer):
    connected_users = set()

    async def connect(self):
        await self.accept()
        await self.channel_layer.group_add("admin_group", self.channel_name)
        self.connected_users.add(self.scope['user'])

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("admin_group", self.channel_name)
        self.connected_users.remove(self.scope['user'])

    async def send_notification(self, event):
        for user in self.connected_users:
            print(user)
            if await sync_to_async(user.has_perm)('blog.view_user'):
                await self.send(text_data=json.dumps({'message': event['message']}))