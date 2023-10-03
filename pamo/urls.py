from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("quoteprint/", include("quote_print.urls")),
    path('admin/', admin.site.urls),
]
