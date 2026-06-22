from django.urls import path
from . import views

urlpatterns = [
    path('', views.login, name='login'),  # ✅ Cambiado de login_view a login
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('index/', views.index, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('ventas/', views.ventas, name='ventas'),
    path('logout/', views.logout_view, name='logout'),
    path('buscar_producto/', views.buscar_producto, name='buscar_producto'),
    path('agregar_producto/', views.agregar_producto, name='agregar_producto'),
    path('delete/<int:id>/', views.delete_producto, name='delete_producto'),
    path('sumar/<int:id>/', views.sumar_stock, name='sumar_stock'),
    path('vender/<int:id>/', views.vender_producto, name='vender_producto'),
    path('venta/', views.registrar_venta, name='registrar_venta'),
    path('reporte_pdf/', views.reporte_pdf, name='reporte_pdf'),
    path('admin_panel/', views.admin_view, name='admin_panel'),
    path('crear_usuario_admin/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('eliminar_usuario/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('crear_inventario/', views.crear_inventario, name='crear_inventario'),
    path('inicializar/', views.inicializar_bd, name='inicializar_bd'),
]
