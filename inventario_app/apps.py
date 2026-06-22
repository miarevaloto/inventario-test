from django.apps import AppConfig

class InventarioAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'inventario_app'
    
    def ready(self):
        # ✅ COMENTADO: No ejecutar init_db aquí porque las tablas aún no existen
        pass