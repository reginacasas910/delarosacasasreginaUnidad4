from django.urls import path
from . import views

urlpatterns = [
    path('', views.inicio, name='inicio'),
    path('contacto/', views.contacto, name='contacto'),
    path('ayuda/', views.ayuda, name='ayuda'),
    path('registro/', views.registro, name='registro'),
    path('login/', views.login_view, name='login'),
    path('recuperar/', views.recuperar, name='recuperar'),
    path('mapa-sitio/', views.mapa_sitio, name='mapa_sitio'),
    path('buscar/', views.buscar, name='buscar'),
    path('maquillaje/', views.maquillaje, name='maquillaje'),
    path('404/', views.buscar, name='404'),
    path('logout/', views.logout_view, name='logout'),
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/productos/<int:id>/', views.api_producto_detalle, name='api_producto_detalle'),
    path('carrito/', views.carrito, name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
]