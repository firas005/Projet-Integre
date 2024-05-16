import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f"chat_{self.conversation_id}"

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        sender = text_data_json.get('sender')
        timestamp = text_data_json.get('timestamp')
        pic = text_data_json.get('pic')
        attachments = text_data_json.get('attachments', [])
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender': sender,
                'timestamp' : timestamp,
                'pic' : pic,
                'attachments': attachments
            }
        )

    async def chat_message(self, event):
        message = event['message']
        sender = event.get('sender')
        timestamp = event.get('timestamp')
        pic = event.get('pic')
        attachments = event.get('attachments', [])
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'sender': sender,
            'timestamp' : timestamp,
            'pic' : pic,
            'attachments': attachments

        }))