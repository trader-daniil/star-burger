from django.urls import path

from .views import product_list_api, banners_list_api, test_template, OrderCreateView
from rest_framework.routers import DefaultRouter


app_name = "foodcartapp"


urlpatterns = [
    path('test/', test_template),
    path('products/', product_list_api),
    path('banners/', banners_list_api, name='banners'),
    path('order/', OrderCreateView.as_view(), name='order')
]
