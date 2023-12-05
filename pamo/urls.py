from django.contrib import admin
from django.urls import path, include

from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as aut_views


urlpatterns = [
    path("quoteprint/", include("quote_print.urls")),
    path("products/", include("products.urls")),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('pamo_bots/', include("pamo_bots.urls")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)