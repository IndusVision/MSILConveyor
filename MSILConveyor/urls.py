import os
from django.conf import settings
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf.urls.static import static
from django.views.static import serve as static_serve

BASE_DIR = settings.BASE_DIR    

schema_view = get_schema_view(
    openapi.Info(
        title="Bar Rate API",
        default_version="v1",
        description="API for managing Bar Rates",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    url = "https://4x86tw12-8002.inc1.devtunnels.ms/"
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('msil_app.urls')),
    
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),  # <-- enable this
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

urlpatterns += [
    re_path(r'^assets/(?P<path>.*)$', static_serve, {
        'document_root': os.path.join(BASE_DIR, 'frontend', 'dist', 'assets'),
    }),
    re_path(r'^(?!assets/).*$', TemplateView.as_view(template_name="index.html")),
]
