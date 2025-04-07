import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Trip
import asyncio


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
                asyncio.create_task(self.send_trip_status_per())
        except Exception as e:
            print(f"Error in connect: {e}")
            self.close()

    async def disconnect(self, close_code):
        if self.user.is_authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name, self.channel_name
            )
            print(f"WebSocket connection closed for user: {self.user.user_id}")
        print(f"WebSocket disconnected with code: {close_code}")

    async def receive(self, text_data):
        try:
            print(f"Received message: {text_data}")
            data = json.loads(text_data)
            if data.get("type") == "get_status":
                trip_data = await self.get_trip_status()
                print(f"Sending trip status: {trip_data}")
                await self.send(text_data=json.dumps(trip_data))
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
        except Exception as e:
            print(f"Error in receive: {e}")

    @database_sync_to_async
    def get_trip_status(self):
        try:
            print(f"Fetching trip status from database for user: {self.user.user_id}")
            trip = (
                Trip.objects.filter(
                    user=self.user, status__in=["active", "paused", "not_started"]
                )
                .order_by("-id")
                .first()
            )

            if trip:
                current_server_time_seconds = 0
                if trip.status == "active":
                    if trip.started_at:
                        current_server_time_seconds = (
                            trip.trip_current_time.total_seconds()
                        )
                    else:
                        current_server_time_seconds = (
                            trip.total_travel_time.total_seconds()
                        )
                        print(
                            f"Warning: Trip {trip.id} is active but started_at is None."
                        )
                else:
                    current_server_time_seconds = trip.total_travel_time.total_seconds()

                trip_status = {
                    "status": trip.status,
                    "started_at": trip.started_at.isoformat()
                    if trip.started_at
                    else None,
                    "paused_at": trip.paused_at.isoformat() if trip.paused_at else None,
                    "ended_at": trip.ended_at.isoformat() if trip.ended_at else None,
                    "total_travel_time": trip.total_travel_time.total_seconds(),
                    "server_time": current_server_time_seconds,
                }
                print(
                    f"Trip status fetched for user {self.user.user_id}: {trip_status}"
                )
                return trip_status
            else:
                last_finished_trip = (
                    Trip.objects.filter(user=self.user, status="finished")
                    .order_by("-ended_at", "-id")
                    .first()
                )
                if last_finished_trip:
                    print(
                        f"No active/paused/not_started trip found for user {self.user.user_id}. Returning last finished trip status."
                    )
                    return {
                        "status": "finished",
                        "started_at": last_finished_trip.started_at.isoformat()
                        if last_finished_trip.started_at
                        else None,
                        "paused_at": last_finished_trip.paused_at.isoformat()
                        if last_finished_trip.paused_at
                        else None,
                        "ended_at": last_finished_trip.ended_at.isoformat()
                        if last_finished_trip.ended_at
                        else None,
                        "total_travel_time": last_finished_trip.total_travel_time.total_seconds(),
                        "server_time": last_finished_trip.total_travel_time.total_seconds(),  # Для завершеної час фіксований
                        "total_cost": str(last_finished_trip.total_amount)
                        if last_finished_trip.total_amount is not None
                        else None,
                    }
                else:
                    print(f"No trip found for user {self.user.user_id}")
                    return {"status": "none", "message": "No trip found"}
        except Exception as e:
            print(f"Error fetching trip status for user {self.user.user_id}: {e}")
            return {"error": "Failed to fetch trip status", "details": str(e)}

    async def trip_status_update(self, event):
        print(f"Trip status update event received: {event}")
        await self.send(text_data=json.dumps(event["data"]))

    async def send_trip_status_per(self):
        while True:
            try:
                print("Sending periodic trip status update")
                trip_data = await self.get_trip_status()
                print(f"Periodic trip status: {trip_data}")
                await self.send(text_data=json.dumps(trip_data))
                await asyncio.sleep(30)
            except Exception as e:
                print(f"Error in send_trip_status_per: {e}")
