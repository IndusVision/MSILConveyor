from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q
from .models import Reports
from datetime import datetime

class ReportsViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_summary="Create Report",
        operation_description="Creates a new report entry. If a record exists with same order_number and clp_number, the new record will have status=False. Sends latest 10 records to reports WebSocket and daily overview to overview WebSocket.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "recorded_date_time": openapi.Schema(type=openapi.TYPE_STRING, description="Date-time string"),
                "order_number": openapi.Schema(type=openapi.TYPE_INTEGER, description="Order number"),
                "clp_number": openapi.Schema(type=openapi.TYPE_INTEGER, description="CLP number"),
            },
            required=["recorded_date_time", "order_number", "clp_number"]
        ),
        responses={201: "Created", 400: "Bad Request"}
    )
    def create(self, request):
        recorded_date_time = request.data.get("recorded_date_time")
        order_number = request.data.get("order_number")
        clp_number = request.data.get("clp_number")

        if None in [recorded_date_time, order_number, clp_number]:
            return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

        # 🔹 Check if record with same order_number + clp_number exists
        exists = Reports.objects.filter(order_number=order_number, clp_number=clp_number).exists()
        status_value = False if exists else True

        # 🔹 Create new record
        Reports.objects.create(
            recorded_date_time=recorded_date_time,
            order_number=order_number,
            clp_number=clp_number,
            status=status_value
        )

        # 🔹 Latest 10 records for reports WebSocket
        latest_records = Reports.objects.order_by('-id')[:10]
        reports_list = [
            {
                "id": r.id,
                "recorded_date_time": r.recorded_date_time,
                "order_number": r.order_number,
                "clp_number": r.clp_number,
                "status": r.status
            } for r in latest_records
        ]
        # 🔹 Broadcast latest 10 records
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "reports_group",
            {
                "type": "send_report",
                "data": reports_list
            }
        )

        # 🔹 Daily overview for Overview WebSocket
        date_only = datetime.strptime(recorded_date_time, "%Y-%m-%dT%H:%M:%S").date()
        daily_records = Reports.objects.filter(
            recorded_date_time__startswith=date_only.strftime("%Y-%m-%d")
        )

        total_boxes = daily_records.count()
        ok_count = daily_records.filter(status=True).count()
        not_ok_count = daily_records.filter(status=False).count()
        latest_record = daily_records.order_by('-id').first()
        latest_clp_number = latest_record.clp_number if latest_record else None
        latest_order_number = latest_record.order_number if latest_record else None

        overview_data = {
            "total_boxes": total_boxes,
            "ok_count": ok_count,
            "not_ok_count": not_ok_count,
            "latest_clp_number": latest_clp_number,
            "latest_order_number": latest_order_number,
        }

        # 
        # Broadcast daily overview
        async_to_sync(channel_layer.group_send)(
            "overview_group",
            {
                "type": "send_overview",
                "data": overview_data
            }
        )

        return Response({
            "message": "Report created successfully",
            "status": status.HTTP_201_CREATED
        }, status=status.HTTP_201_CREATED)
