from django.core.management.base import BaseCommand
from vetweb.models import Carrito, CarritoItem
from django.db import transaction

class Command(BaseCommand):
    help = 'Limpia carritos huérfanos y corrige problemas en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Forzar la limpieza sin confirmación',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando limpieza de carritos...'))
        
        # Contar carritos antes de la limpieza
        carritos_antes = Carrito.objects.count()
        items_antes = CarritoItem.objects.count()
        
        with transaction.atomic():
            # Eliminar carritos sin usuario
            carritos_sin_usuario = Carrito.objects.filter(user__isnull=True)
            carritos_eliminados = carritos_sin_usuario.count()
            carritos_sin_usuario.delete()
            
            # Eliminar items sin carrito
            items_sin_carrito = CarritoItem.objects.filter(carrito__isnull=True)
            items_eliminados = items_sin_carrito.count()
            items_sin_carrito.delete()
            
            # Eliminar items con productos que no existen
            items_producto_inexistente = CarritoItem.objects.filter(producto__isnull=True)
            items_producto_eliminados = items_producto_inexistente.count()
            items_producto_inexistente.delete()
        
        # Contar después de la limpieza
        carritos_despues = Carrito.objects.count()
        items_despues = CarritoItem.objects.count()
        
        self.stdout.write(self.style.SUCCESS(f'Limpieza completada:'))
        self.stdout.write(f'  - Carritos eliminados: {carritos_eliminados}')
        self.stdout.write(f'  - Items sin carrito eliminados: {items_eliminados}')
        self.stdout.write(f'  - Items con producto inexistente eliminados: {items_producto_eliminados}')
        self.stdout.write(f'  - Carritos restantes: {carritos_despues}')
        self.stdout.write(f'  - Items restantes: {items_despues}')
        
        # Verificar carritos sin items
        carritos_vacios = Carrito.objects.filter(items__isnull=True).count()
        if carritos_vacios > 0:
            self.stdout.write(self.style.WARNING(f'  - Carritos vacíos encontrados: {carritos_vacios}'))
        
        self.stdout.write(self.style.SUCCESS('¡Limpieza completada exitosamente!')) 