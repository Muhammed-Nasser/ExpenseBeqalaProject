from django.urls import include, path
from rest_framework import routers
from . import views
from location.views import ListStore
router = routers.DefaultRouter()

urlpatterns = [
    path('', include(router.urls)),
    path('store/', views.storeApi),
    path('category/', views.storecategoryApi),
    path('prices/', views.priceApi),
   
    ]