from rest_framework import viewsets, status
from rest_framework.response import Response
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Q
from .models import Reports
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor


class ReportsViewSet(viewsets.ViewSet):
    @swagger_auto_schema(
        operation_summary="Create Report",
        operation_description="Creates a new report entry. If a record exists with same order_number and clp_number, or either value is 0/null, the new record will have status=False (NOK). Sends latest 10 records to reports WebSocket and daily overview to overview WebSocket.",
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

        # Convert to int safely
        try:
            order_number = int(order_number)
            clp_number = int(clp_number)
        except (TypeError, ValueError):
            return Response({"error": "Invalid order_number or clp_number"}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ Check if either order_number or clp_number is 0 or null-like
        if order_number == 0 or clp_number == 0:
            status_value = False
        else:
            # Check if record with same order_number + clp_number exists
            exists = Reports.objects.filter(order_number=order_number, clp_number=clp_number).exists()
            status_value = False if exists else True

        # Create new record
        report = Reports.objects.create(
            recorded_date_time=recorded_date_time,
            order_number=order_number,
            clp_number=clp_number,
            status=status_value
        )

        # Latest 10 records for reports WebSocket
        latest_records = Reports.objects.order_by('-id')[:10]
        latest_records = reversed(latest_records)  # newest first

        reports_list = [
            {
                "id": r.id,
                "recorded_date_time": r.recorded_date_time,
                "order_number": r.order_number,
                "clp_number": r.clp_number,
                "status": "OK" if r.status else "NOK"
            } for r in latest_records
        ]

        expected_count_obj = ExpectedCount.objects.order_by('-id').first()
        expected_count = expected_count_obj.expected_count if expected_count_obj else 0

        # Broadcast latest 10 records
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "reports_group",
            {
                "type": "send_report",
                "data": reports_list
            }
        )

        # Daily overview for Overview WebSocket
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
            'expected_count': expected_count
        }

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

# class ReportsViewSet(viewsets.ViewSet):
#     @swagger_auto_schema(
#         operation_summary="Create Report",
#         operation_description="Creates a new report entry. Sends latest 10 records, daily overview, and expected count via WebSocket.",
#         request_body=openapi.Schema(
#             type=openapi.TYPE_OBJECT,
#             properties={
#                 "recorded_date_time": openapi.Schema(type=openapi.TYPE_STRING, description="Date-time string"),
#                 "order_number": openapi.Schema(type=openapi.TYPE_INTEGER, description="Order number"),
#                 "clp_number": openapi.Schema(type=openapi.TYPE_INTEGER, description="CLP number"),
#             },
#             required=["recorded_date_time", "order_number", "clp_number"]
#         ),
#         responses={201: "Created", 400: "Bad Request"}
#     )
#     def create(self, request):
#         recorded_date_time = request.data.get("recorded_date_time")
#         order_number = request.data.get("order_number")
#         clp_number = request.data.get("clp_number")

#         if None in [recorded_date_time, order_number, clp_number]:
#             return Response({"error": "Missing fields"}, status=status.HTTP_400_BAD_REQUEST)

#         # Check if record with same order_number + clp_number exists
#         exists = Reports.objects.filter(order_number=order_number, clp_number=clp_number).exists()
#         status_value = False if exists else True

#         # Create new report record
#         report = Reports.objects.create(
#             recorded_date_time=recorded_date_time,
#             order_number=order_number,
#             clp_number=clp_number,
#             status=status_value
#         )

#         # Latest 10 records for reports WebSocket
#         latest_records = Reports.objects.order_by('-id')[:10]
#         reports_list = [
#             {
#                 "id": r.id,
#                 "recorded_date_time": r.recorded_date_time,
#                 "order_number": r.order_number,
#                 "clp_number": r.clp_number,
#                 "status": "OK" if r.status else "NOK"
#             } for r in latest_records
#         ]

#         # Get expected count (latest row from ExpectedCount table)
#         expected_count_obj = ExpectedCount.objects.order_by('-id').first()
#         expected_count = expected_count_obj.expected_count if expected_count_obj else 0

#         # Broadcast latest 10 records + expected count
#         channel_layer = get_channel_layer()
#         async_to_sync(channel_layer.group_send)(
#             "reports_group",
#             {
#                 "type": "send_report",
#                 "data": {
#                     "latest_reports": reports_list,
#                     "expected_count": expected_count
#                 }
#             }
#         )

#         # Daily overview for Overview WebSocket
#         date_only = datetime.strptime(recorded_date_time, "%Y-%m-%dT%H:%M:%S").date()
#         daily_records = Reports.objects.filter(
#             recorded_date_time__startswith=date_only.strftime("%Y-%m-%d")
#         )

#         total_boxes = daily_records.count()
#         ok_count = daily_records.filter(status=True).count()
#         not_ok_count = daily_records.filter(status=False).count()
#         latest_record = daily_records.order_by('-id').first()
#         latest_clp_number = latest_record.clp_number if latest_record else None
#         latest_order_number = latest_record.order_number if latest_record else None

#         overview_data = {
#             "total_boxes": total_boxes,
#             "ok_count": ok_count,
#             "not_ok_count": not_ok_count,
#             "latest_clp_number": latest_clp_number,
#             "latest_order_number": latest_order_number,
#             "expected_count": expected_count  # include expected count here
#         }

#         # Broadcast daily overview
#         async_to_sync(channel_layer.group_send)(
#             "overview_group",
#             {
#                 "type": "send_overview",
#                 "data": overview_data
#             }
#         )

#         return Response({
#             "message": "Report created successfully",
#             "status": status.HTTP_201_CREATED,
#             "expected_count": expected_count
#         }, status=status.HTTP_201_CREATED)

from rest_framework import viewsets
from rest_framework.response import Response
from multiprocessing import Pool, cpu_count
from .models import Reports, ExpectedData

# Helper function for multiprocessing
def check_record_multiproc(record, db_records_set):
    if record not in db_records_set:
        return record
    return None

class ReportCompare(viewsets.ViewSet):
    """
    Compare all records in ExpectedData against Reports and return missing records.
    """

    def list(self, request):
        # 1. Fetch expected data
        expected_records_qs = ExpectedData.objects.all().values_list("order_number", "clp_number")
        expected_records = set((r[0], r[1]) for r in expected_records_qs)

        if not expected_records:
            return Response({"message": "No expected data available"}, status=200)

        # 2. Fetch reports data
        reports_records_qs = Reports.objects.all().values_list("order_number", "clp_number")
        reports_records = set((r[0], r[1]) for r in reports_records_qs)

        # 3. Compare using multiprocessing
        cpu_cores = min(cpu_count(), len(expected_records))
        with Pool(processes=cpu_cores) as pool:
            results = pool.starmap(
                check_record_multiproc,
                [(record, reports_records) for record in expected_records]
            )

        missing = [r for r in results if r is not None]

        # 4. Prepare response
        response_data = {
            "missing_records": [{"order_number": r[0], "clp_number": r[1]} for r in missing]
        }

        return Response(response_data)





from django.shortcuts import render
from django.views import View

class CameraView(View):
    def get(self, request):
        return render(request, "camera_stream.html")


import io
import pandas as pd
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import ExpectedData, ExpectedCount

class ExpectedDataUploadViewSet(viewsets.ViewSet):
    """
    Upload a CSV/Excel file, save Document Number and Handling Unit to ExpectedData,
    and update ExpectedCount with the total number of rows.
    """
    parser_classes = [MultiPartParser, FormParser]

    @swagger_auto_schema(
        operation_description="Upload CSV/Excel file and save Document Number + Handling Unit",
        manual_parameters=[
            openapi.Parameter(
                name="file",
                in_=openapi.IN_FORM,
                type=openapi.TYPE_FILE,
                description="CSV or Excel file containing 'Document Number' and 'Handling Unit'",
                required=True
            ),
        ],
        responses={200: "Data saved successfully", 400: "File missing or invalid"}
    )
    def create(self, request):
        file = request.FILES.get("file")
        if not file:
            return Response({"error": "Please upload a file"}, status=status.HTTP_400_BAD_REQUEST)

        skipped_rows = []

        # 1. Read CSV/Excel safely
        try:
            if file.name.endswith(".csv"):
                raw_bytes = file.read()
                try:
                    decoded = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    decoded = raw_bytes.decode("latin1")
                file_stream = io.StringIO(decoded)
                df = pd.read_csv(file_stream, engine='python', on_bad_lines='skip')
            elif file.name.endswith((".xls", ".xlsx")):
                df = pd.read_excel(file)
            else:
                return Response({"error": "Unsupported file format"}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Failed to read file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Check required columns exist
        required_cols = {"Document Number", "Handling Unit"}
        if not required_cols.issubset(df.columns):
            return Response({"error": f"File must have {', '.join(required_cols)} columns"}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Filter only relevant columns
        df_filtered = df[["Document Number", "Handling Unit"]].copy()
        df_filtered.rename(columns={"Document Number": "order_number", "Handling Unit": "clp_number"}, inplace=True)

        # 4. Clear old ExpectedData
        ExpectedData.objects.all().delete()

        # 5. Save new ExpectedData
        bulk_data = []
        for idx, row in df_filtered.iterrows():
            try:
                bulk_data.append(ExpectedData(order_number=row['order_number'], clp_number=row['clp_number']))
            except Exception:
                skipped_rows.append(idx + 2)
                continue

        ExpectedData.objects.bulk_create(bulk_data)

        # 6. Update ExpectedCount (replace old value)
        total_rows = len(bulk_data)
        ExpectedCount.objects.all().delete()
        ExpectedCount.objects.create(expected_count=total_rows)

        response_data = {
            "message": "Data saved successfully",
            "total_rows": total_rows
        }
        if skipped_rows:
            response_data["skipped_rows"] = skipped_rows

        return Response(response_data, status=status.HTTP_200_OK)
