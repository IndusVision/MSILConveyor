import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ReportsConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("reports_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("reports_group", self.channel_name)

    async def send_report(self, event):
        # event["data"] is now a list of latest 10 records
        await self.send(text_data=json.dumps(event["data"]))


class StartConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # All clients join the same group
        await self.channel_layer.group_add("start_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("start_group", self.channel_name)

    # Receive message from a client
    async def receive(self, text_data):
        data = json.loads(text_data)

        # If either start or stop is True, broadcast to group
        if data.get("start") is True or data.get("stop") is True:
            await self.channel_layer.group_send(
                "start_group",
                {
                    "type": "broadcast_action",
                    "data": data
                }
            )

    # Broadcast message to all clients
    async def broadcast_action(self, event):
        await self.send(text_data=json.dumps(event["data"]))

        

class OverviewConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.channel_layer.group_add("overview_group", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard("overview_group", self.channel_name)

    # Receive broadcast data
    async def send_overview(self, event):
        await self.send(text_data=json.dumps(event["data"]))
        
        
import cv2
import base64
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer

RTSP_URL = "rtsp://admin:1234@192.168.1.36:8080/h264_ulaw.sdp"

class CameraStreamConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.streaming = True
        self.task = asyncio.create_task(self.stream_video())

    async def disconnect(self, close_code):
        self.streaming = False
        if hasattr(self, "task") and self.task:
            self.task.cancel()

    async def stream_video(self):
        cap = cv2.VideoCapture(RTSP_URL)
        if not cap.isOpened():
            await self.send_json({"error": "Unable to open RTSP stream"})
            return

        while self.streaming:
            ret, frame = cap.read()
            if not ret:
                await asyncio.sleep(0.01)  # retry quickly if frame fails
                continue

            _, buffer = cv2.imencode('.jpg', frame)
            frame_b64 = base64.b64encode(buffer).decode("utf-8")

            await self.send_json({"frame": frame_b64})

            # Faster FPS
            await asyncio.sleep(0.02)  # ~50 FPS

        cap.release()
        await self.send_json({"message": "Streaming ended"})

    async def send_json(self, content):
        import json
        await self.send(text_data=json.dumps(content))
