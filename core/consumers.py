import json
import asyncio
import uuid
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from support.models import Message as ChatMessage
from get_direction.models import Trip


class UserActivityConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("Consumer connect called")
        try:
            self.user = self.scope["user"]
            print(
                f"User found: {self.user}, Authenticated: {self.user.is_authenticated}"
            )

            self.active_chat_groups = set()

            if not self.user or not self.user.is_authenticated:
                print("User not authenticated, closing connection.")
                await self.close()
                return

            self.user_group_name = f"user_{self.user.user_id}"
            print(f"User group name: {self.user_group_name}")

            print("Attempting group_add...")
            await self.channel_layer.group_add(self.user_group_name, self.channel_name)
            print("group_add successful")

            print("Attempting accept...")
            await self.accept()
            print(
                f"UserActivityConsumer connected for user {self.user.user_id}, channel: {self.channel_name}"
            )

            self.trip_status_task = asyncio.create_task(
                self.send_trip_status_periodically()
            )

            await self.send_json({"type": "connection_ready"})
        except Exception as e:
            print(f"!!! EXCEPTION IN CONNECT: {e}")
            import traceback

            traceback.print_exc()
            await self.close(code=4001)
            raise

    async def disconnect(self, close_code):
        print(
            f"UserActivityConsumer disconnecting for user {self.user.user_id}, code: {close_code}"
        )

        if hasattr(self, "trip_status_task"):
            self.trip_status_task.cancel()
            try:
                await self.trip_status_task
            except asyncio.CancelledError:
                print("Trip status task cancelled successfully.")

        await self.channel_layer.group_discard(self.user_group_name, self.channel_name)
        for group_name in list(self.active_chat_groups):
            await self._leave_chat_group(group_name)

        print(f"UserActivityConsumer disconnected for user {self.user.user_id}")

    async def receive(self, text_data=None, bytes_data=None):
        """
        Обробляє повідомлення, отримані від клієнта.
        """
        print(f"Raw text_data received for user {self.user.user_id}: {text_data}")
        if not text_data:
            return

        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            payload = data.get("payload", {})

            print(
                f"Received message type: {message_type} from user {self.user.user_id}"
            )

            # --- Routing incoming messages from the client ---
            if message_type == "get_trip_status":
                await self.handle_get_trip_status()
            elif message_type == "send_chat_message":
                await self.handle_send_chat_message(payload)
            elif message_type == "join_chat":
                await self.handle_join_chat(payload)
            elif message_type == "leave_chat":
                await self.handle_leave_chat(payload)
            else:
                await self.send_error(f"Unknown message type: {message_type}")

        except json.JSONDecodeError:
            await self.send_error("Invalid JSON received.")
        except Exception as e:
            print(f"Error in receive for user {self.user.user_id}: {e}")
            import traceback

            traceback.print_exc()
            await self.send_error("An internal server error occurred.")

    # --- Trip Status Handlers---

    @database_sync_to_async
    def _get_trip_status_data(self):
        """Асинхронно отримує дані поточної або останньої поїздки з БД."""
        try:
            trip = (
                Trip.objects.filter(
                    user=self.user, status__in=["active", "paused", "not_started"]
                )
                .order_by("-id")
                .first()
            )

            if trip:
                current_server_time_seconds = 0
                if trip.status == "active" and trip.started_at:
                    current_server_time_seconds = trip.trip_current_time.total_seconds()
                else:
                    current_server_time_seconds = trip.total_travel_time.total_seconds()
                    if trip.status == "active" and not trip.started_at:
                        print(f"Warning: Trip {trip.id} active but started_at is None.")

                prepaid_seconds = (trip.prepaid_minutes or 0) * 60
                if (
                    current_server_time_seconds > prepaid_seconds
                    and prepaid_seconds > 0
                ):
                    trip.status = "finished"
                    trip.save()

                trip_status = {
                    "status": trip.status,
                    "started_at": trip.started_at.isoformat()
                    if trip.started_at
                    else None,
                    "paused_at": trip.paused_at.isoformat() if trip.paused_at else None,
                    "ended_at": trip.ended_at.isoformat() if trip.ended_at else None,
                    "total_travel_time": trip.total_travel_time.total_seconds(),
                    "server_time": current_server_time_seconds,
                    "total_cost": float(trip.total_amount)
                    if trip.total_amount is not None
                    else 0.0,
                }
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
                        "server_time": last_finished_trip.total_travel_time.total_seconds(),
                        "total_cost": float(last_finished_trip.total_amount)
                        if last_finished_trip.total_amount is not None
                        else 0.0,
                    }
                else:
                    print(f"No trip found for user {self.user.user_id}")
                    return {"status": "none", "message": "No trip found"}
        except Exception as e:
            print(f"Error fetching trip status for user {self.user.user_id}: {e}")
            return {"error": "Failed to fetch trip status", "details": str(e)}

    async def handle_get_trip_status(self):
        """Sending current trip status."""
        trip_data = await self._get_trip_status_data()
        await self.send_json({"type": "trip_status", "data": trip_data})

    async def send_trip_status_periodically(self):
        """Periodically sends the trip status while the connection is active."""
        while True:
            try:
                trip_data = await self._get_trip_status_data()
                current_status = trip_data.get("status")

                await self.send_json({"type": "trip_status", "data": trip_data})

                if current_status in ["none", "finished"]:
                    print(
                        f"Stopping periodic trip updates for user {self.user.user_id}, status: {current_status}"
                    )
                    break

                await asyncio.sleep(5)

            except asyncio.CancelledError:
                print(
                    f"Periodic trip update task cancelled for user {self.user.user_id}"
                )
                raise
            except Exception as e:
                print(
                    f"Error in periodic trip update for user {self.user.user_id}: {e}"
                )
                await asyncio.sleep(15)

    # --- Chat Handlers---

    @database_sync_to_async
    def _save_chat_message(self, chat_id_uuid, message_content):
        try:
            message_obj = ChatMessage.objects.create(
                chat_id=chat_id_uuid, sender=self.user, content=message_content
            )
            return {
                "message": message_obj.content,
                "user": self.user.username,
                "user_id": self.user.user_id,
                "created_at": message_obj.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "message_id": str(message_obj.id),
            }
        except Exception as e:
            print(f"DB Error saving chat message for user {self.user.user_id}: {e}")
            return None

    async def handle_send_chat_message(self, payload):
        message_content = payload.get("message")
        chat_id_str = payload.get("chat_id")

        if not message_content or not chat_id_str:
            await self.send_error("Missing 'message' or 'chat_id' in payload")
            return

        try:
            chat_id_uuid = uuid.UUID(chat_id_str)
        except ValueError:
            await self.send_error(f"Invalid chat_id format: {chat_id_str}")
            return

        message_data = await self._save_chat_message(chat_id_uuid, message_content)

        if message_data:
            chat_group_name = f"chat_{chat_id_str}"
            await self.channel_layer.group_send(
                chat_group_name,
                {
                    "type": "chat_message_broadcast",
                    "data": message_data,
                    "user": self.user.username,
                    "created_at": message_data["created_at"],
                },
            )
        else:
            await self.send_error("Failed to save chat message.")

    async def _join_chat_group(self, chat_id_str):
        chat_group_name = f"chat_{chat_id_str}"

        if chat_group_name not in self.active_chat_groups:
            await self.channel_layer.group_add(chat_group_name, self.channel_name)
            print(f"Joined to the {chat_group_name}")
            self.active_chat_groups.add(chat_group_name)
            await self.send_json({"type": "chat_joined", "chat_id": chat_id_str})
        else:
            print(f"User {self.user.user_id} already in chat group {chat_group_name}")

    async def _leave_chat_group(self, chat_id_str):
        chat_group_name = f"chat_{chat_id_str}"
        if chat_group_name in self.active_chat_groups:
            await self.channel_layer.group_discard(chat_group_name, self.channel_name)
            self.active_chat_groups.discard(chat_group_name)
            await self.send_json({"type": "chat_left", "chat_id": chat_id_str})

    async def handle_join_chat(self, payload):
        chat_id_str = payload.get("chat_id")
        if not chat_id_str:
            await self.send_error("Missing 'chat_id' in payload for join_chat")
            return
        try:
            uuid.UUID(chat_id_str)
            await self._join_chat_group(chat_id_str)
        except ValueError:
            await self.send_error(f"Invalid chat_id format: {chat_id_str}")

    async def handle_leave_chat(self, payload):
        """Handles the client's request to leave a chat group."""
        chat_id_str = payload.get("chat_id")
        if not chat_id_str:
            await self.send_error("Missing 'chat_id' in payload for leave_chat")
            return
        await self._leave_chat_group(chat_id_str)

    async def trip_status_update(self, event):
        """
        Обробляє зовнішнє оновлення статусу поїздки (надіслане до user_{id}).
        Наприклад, якщо статус змінюється через дію адміністратора або інший процес.
        """
        print(
            f"Received external trip_status_update event for user {self.user.user_id}"
        )
        await self.send_json({"type": "trip_status", "data": event["data"]})

    async def chat_message_broadcast(self, event):
        """
        Handles a chat message sent to the group chat_{id},
        of which this consumer is a member. Sends the data to the client.
        """
        try:
            message_payload = event["data"]
            print(
                f"Broadcasting chat message data to user {self.user.user_id}: {message_payload}"
            )
            await self.send_json({"type": "chat_message", "data": message_payload})
        except KeyError as e:
            print(
                f"Error processing chat_message_broadcast event: Missing key {e} in event={event}"
            )
        except Exception as e:
            print(f"Error in chat_message_broadcast for user {self.user.user_id}: {e}")
            import traceback

            traceback.print_exc()

    async def user_notification(self, event):
        """Обробляє загальне сповіщення для користувача."""
        print(f"Sending user_notification to user {self.user.user_id}")
        await self.send_json({"type": "notification", "data": event["message"]})

    async def balance_update_notification(self, event):
        """Обробляє сповіщення про оновлення балансу."""
        print(f"Sending balance_update_notification to user {self.user.user_id}")
        await self.send_json(
            {"type": "balance_update", "balance": str(event["balance"])}
        )

    async def send_json(self, data):
        try:
            await self.send(text_data=json.dumps(data))
        except Exception as e:
            print(f"Error sending JSON to user {self.user.user_id}: {e}")

    async def send_error(self, message):
        await self.send_json({"type": "error", "message": message})
