from django.core.management.base import BaseCommand
from vetweb.models import Carrito, CarritoItem, User
from django.contrib.auth.models import User as AuthUser

class Command(BaseCommand):
    help = 'Diagnostica el carrito de un usuario específico'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Nombre de usuario')

    def handle(self, *args, **options):
        username = options['username']
        
        try:
            user = AuthUser.objects.get(username=username)
            self.stdout.write(f'Usuario encontrado: {user.username} (ID: {user.id})')
            
            # Verificar si tiene carrito
            try:
                carrito = Carrito.objects.get(user=user)
                self.stdout.write(f'✅ Carrito encontrado: ID {carrito.id}')
                
                # Contar items
                items_count = carrito.items.count()
                self.stdout.write(f'📦 Items en carrito: {items_count}')
                
                if items_count > 0:
                    self.stdout.write('Productos en el carrito:')
                    for item in carrito.items.all():
                        self.stdout.write(f'  - {item.producto.nombre} (x{item.cantidad}) - ${item.get_subtotal()}')
                    
                    # Calcular totales
                    subtotal = carrito.get_subtotal()
                    iva = carrito.get_iva()
                    total = carrito.get_total()
                    
                    self.stdout.write(f'💰 Subtotal: ${subtotal}')
                    self.stdout.write(f'💰 IVA: ${iva}')
                    self.stdout.write(f'💰 Total: ${total}')
                else:
                    self.stdout.write('⚠️ El carrito está vacío')
                    
            except Carrito.DoesNotExist:
                self.stdout.write('❌ El usuario no tiene carrito')
                
        except AuthUser.DoesNotExist:
            self.stdout.write(f'❌ Usuario "{username}" no encontrado') 