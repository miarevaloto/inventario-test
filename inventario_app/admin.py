from django.contrib import admin
from .models import Inventario, Producto, Venta

admin.site.register(Inventario)
admin.site.register(Producto)
admin.site.register(Venta)