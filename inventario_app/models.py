from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Inventario(models.Model):
    nombre = models.CharField(max_length=120)
    
    def __str__(self):
        return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=120)
    categoria = models.CharField(max_length=120)
    cantidad = models.IntegerField()
    precio = models.FloatField()
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.nombre} - {self.cantidad} und."
    
    @property
    def valor_total(self):
        return self.cantidad * self.precio

class Venta(models.Model):
    producto = models.CharField(max_length=120)
    cantidad = models.IntegerField()
    precio = models.FloatField()
    fecha = models.DateTimeField(auto_now_add=True)
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.producto} - {self.cantidad} und."
    
    @property
    def total(self):
        return self.cantidad * self.precio

# ✅ MODELO PARA RELACIONAR USUARIO CON INVENTARIO
class UsuarioInventario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    inventario = models.ForeignKey(Inventario, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.usuario.email} -> {self.inventario.nombre}"