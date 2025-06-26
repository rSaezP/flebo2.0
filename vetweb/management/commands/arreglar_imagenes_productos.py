from django.core.management.base import BaseCommand
from vetweb.models import Producto
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Arregla las referencias de imágenes de productos que se perdieron después del pull'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mostrar qué se haría sin hacer cambios',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando arreglo de imágenes de productos...'))
        
        # Obtener todos los productos
        productos = Producto.objects.all()
        productos_sin_imagen = productos.filter(imagen='')
        productos_con_imagen = productos.exclude(imagen='')
        
        self.stdout.write(f'Total de productos: {productos.count()}')
        self.stdout.write(f'Productos sin imagen: {productos_sin_imagen.count()}')
        self.stdout.write(f'Productos con imagen: {productos_con_imagen.count()}')
        
        # Lista de archivos de imagen disponibles
        media_path = os.path.join(settings.MEDIA_ROOT, 'productos')
        if os.path.exists(media_path):
            archivos_disponibles = [f for f in os.listdir(media_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            self.stdout.write(f'Archivos de imagen disponibles: {len(archivos_disponibles)}')
            self.stdout.write(f'Archivos: {archivos_disponibles}')
        else:
            self.stdout.write(self.style.ERROR(f'Directorio de media no encontrado: {media_path}'))
            return
        
        # Mapeo de nombres de productos a archivos de imagen
        mapeo_productos = {
            'producto1': 'producto1.png',
            'producto2': 'producto2.jpg', 
            'producto3': 'producto3.png',
            'producto4': 'producto4.png',
            'producto5': 'producto5.jpeg',
            'bio': 'bio.jpg',
            'pcr': 'pcr.png',
            'test': 'testerapidos.JPG',
            'pointcare': 'pointcarev3.JPG',
            'hv-fia': 'hv-fia-3000.jpg',
            'aco': 'ACO-7100-coagulacion.png',
        }
        
        # Arreglar productos sin imagen
        for producto in productos_sin_imagen:
            nombre_lower = producto.nombre.lower()
            imagen_asignada = None
            
            # Buscar coincidencia en el mapeo
            for clave, archivo in mapeo_productos.items():
                if clave in nombre_lower and archivo in archivos_disponibles:
                    imagen_asignada = f'productos/{archivo}'
                    break
            
            # Si no hay coincidencia específica, buscar por nombre del archivo
            if not imagen_asignada:
                for archivo in archivos_disponibles:
                    if archivo.lower().startswith(nombre_lower.replace(' ', '')):
                        imagen_asignada = f'productos/{archivo}'
                        break
            
            if imagen_asignada:
                if not options['dry_run']:
                    producto.imagen = imagen_asignada
                    producto.save()
                    self.stdout.write(f'✅ Asignada imagen "{imagen_asignada}" a "{producto.nombre}"')
                else:
                    self.stdout.write(f'🔍 Se asignaría imagen "{imagen_asignada}" a "{producto.nombre}"')
            else:
                self.stdout.write(self.style.WARNING(f'⚠️ No se encontró imagen para "{producto.nombre}"'))
        
        # Verificar productos con imagen
        for producto in productos_con_imagen:
            ruta_imagen = os.path.join(settings.MEDIA_ROOT, str(producto.imagen))
            if not os.path.exists(ruta_imagen):
                self.stdout.write(self.style.ERROR(f'❌ Imagen no encontrada para "{producto.nombre}": {producto.imagen}'))
                if not options['dry_run']:
                    producto.imagen = ''
                    producto.save()
                    self.stdout.write(f'🔄 Limpiada referencia de imagen para "{producto.nombre}"')
        
        self.stdout.write(self.style.SUCCESS('¡Arreglo de imágenes completado!')) 