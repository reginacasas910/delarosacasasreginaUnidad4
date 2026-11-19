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

    # API propia
    path('api/productos/', views.api_productos, name='api_productos'),
    path('api/productos/<int:id>/', views.api_producto_detalle, name='api_producto_detalle'),

    # Carrito de compras
    path('carrito/', views.carrito, name='carrito'),
    path('carrito/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('carrito/eliminar/<int:producto_id>/', views.eliminar_del_carrito, name='eliminar_del_carrito'),
    path('carrito/actualizar/<int:producto_id>/', views.actualizar_carrito, name='actualizar_carrito'),

    # Pagos Stripe
    path('carrito/pagar/', views.crear_pago, name='crear_pago'),
    path('pago/exitoso/', views.pago_exitoso, name='pago_exitoso'),
    path('pago/cancelado/', views.pago_cancelado, name='pago_cancelado'),
]