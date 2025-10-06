from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportsViewSet,ReportCompare,CameraView,ExpectedDataUploadViewSet

router = DefaultRouter()
router.register(r'reports', ReportsViewSet, basename="reports")
router.register('report-compare',ReportCompare,basename="report-compare")
router.register(r'expected-data',ExpectedDataUploadViewSet,basename='expected-data')
urlpatterns = [
    path("", include(router.urls)),
    path('camera/', CameraView.as_view(), name='camera_stream'),
]
