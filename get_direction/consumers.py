import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Trip


class TripConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        try:
            self.user = self.scope["user"]
            if not self.user.is_authenticated:
                print("User not authenticated")
                self.close()
            else:
                self.room_group_name = f"user_{self.user.user_id}"
                await self.channel_layer.group_add(
                    self.room_group_name, self.channel_name
                )
                await self.accept()
                print(f"WebSocket connection established for user: {self.user.user_id}")
        except Exception as e:
            print(f"Error in connect: {e}")
            self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            print(f"WebSocket connection closed for user: {self.user.user_id}")

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            if data.get("type") == "get_status":
                trip_data = await self.get_trip_status()
                await self.send(text_data=json.dumps(trip_data))
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")

    @database_sync_to_async
    def get_trip_status(self):
        try:
            trip = Trip.objects.filter(user=self.user).first()
            if trip:
                return {
                    "status": trip.status,
                    "started_at": trip.started_at.isoformat(),
                    "paused_at": trip.paused_at.isoformat() if trip.paused_at else None,
                    "ended_at": trip.ended_at.isoformat() if trip.ended_at else None,
                    "total_travel_time": trip.total_travel_time.total_seconds(),
                }
            else:
                return {"error": "No trip found"}
        except Exception as e:
            print(f"Error fetching trip status: {e}")
            return {"error": "Failed to fetch trip status"}

    async def trip_status_update(self, event):
        await self.send(text_data=json.dumps(event["data"]))
