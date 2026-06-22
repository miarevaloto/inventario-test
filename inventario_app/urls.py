from django.urls import path
from . import views

urlpatterns = [
    # ========== AUTENTICACIÓN ==========
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # ========== INVENTARIO ==========
    path('index/', views.index, name='index'),
    path('buscar_producto/', views.buscar_producto, name='buscar_producto'),
    path('agregar_producto/', views.agregar_producto, name='agregar_producto'),
    path('delete/<int:id>/', views.delete_producto, name='delete_producto'),
    path('sumar/<int:id>/', views.sumar_stock, name='sumar_stock'),
    path('vender/<int:id>/', views.vender_producto, name='vender_producto'),
    
    # ========== VENTAS ==========
    path('ventas/', views.ventas, name='ventas'),
    path('venta/', views.registrar_venta, name='registrar_venta'),
    
    # ========== DASHBOARD Y REPORTES ==========
    path('dashboard/', views.dashboard, name='dashboard'),
    path('reporte_pdf/', views.reporte_pdf, name='reporte_pdf'),
    
    # ========== ADMIN ==========
    path('admin_panel/', views.admin_view, name='admin_panel'),
    path('crear_usuario_admin/', views.crear_usuario_admin, name='crear_usuario_admin'),
    path('eliminar_usuario/<int:id>/', views.eliminar_usuario, name='eliminar_usuario'),
    path('crear_inventario/', views.crear_inventario, name='crear_inventario'),
    
    # ========== INICIALIZACIÓN ==========
    path('crear_admin/', views.crear_admin_sin_login, name='crear_admin'),
    path('crear_todo/', views.crear_todo, name='crear_todo'),
]
