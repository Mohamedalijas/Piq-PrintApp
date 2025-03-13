from django.contrib import admin
from django.urls import path,include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("app1.urls")),
    path('',lambda request: redirect('login'))
]
