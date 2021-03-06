from django.urls import include, path
from rest_framework import routers
from . import views
router = routers.DefaultRouter()

urlpatterns = [
    
    path('', include(router.urls)),
    path('product/', views.productApi),
    path('product/<str:pk>', views.individualProduct),
    path('category/', views.categoryApi),
    path('brand/', views.brandApi),
]
