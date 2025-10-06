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

        # Only broadcast if start is True
        if data.get("start") is True:
            await self.channel_layer.group_send(
                "start_group",
                {
                    "type": "send_start",
                    "data": data
                }
            )

    # Broadcast message to all clients
    async def send_start(self, event):
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