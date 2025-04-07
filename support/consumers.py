import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .models import Message
import uuid


class ChatConsumer(WebsocketConsumer):
    def connect(self):
        try:
            self.chat_id = self.scope["url_route"]["kwargs"]["chat_id"]
            self.room_group_name = f"chat_{self.chat_id}"

            print(f"Connecting to chat_id: {self.chat_id}")

            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name, self.channel_name
            )

            self.accept()
            print("WebSocket connection established")
        except Exception as e:
            print(f"Error in connect: {e}")
            self.close()

    def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message = text_data_json.get("message")
            chat_id_str = text_data_json.get("chat_id")

            if not message or not chat_id_str:
                print("Missing message or chat_id")
                return

            try:
                chat_id = uuid.UUID(chat_id_str)
            except ValueError:
                print(f"Invalid UUID: {chat_id_str}")
                return

            user = self.scope.get("user")
            print(f"Received message from user: {user}, chat_id: {chat_id}")

            if not user or not user.is_authenticated:
                print("Error: Unauthenticated user")
                return

            message_obj = Message.objects.create(
                chat_id=chat_id, sender=user, content=message
            )
            print(f"Message saved: {message_obj}")

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    "type": "chat_message",
                    "message": message,
                    "user": user.username,
                    "created_at": message_obj.created_at.strftime("%d %b %Y, %H:%M"),
                },
            )
        except Exception as e:
            print(f"Error in receive: {e}")

    def chat_message(self, event):
        try:
            print(f"Sending message: {event}")
            self.send(
                text_data=json.dumps(
                    {
                        "type": "chat",
                        "message": event["message"],
                        "username": event["user"],
                        "created_at": event["created_at"],
                    }
                )
            )
        except Exception as e:
            print(f"Error in chat_message: {e}")

    def disconnect(self, close_code):
        try:
            print(f"Connection closed with code {close_code}")
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )
        except Exception as e:
            print(f"Error in disconnect: {e}")
