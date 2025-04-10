from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.validators import MinValueValidator

def get_pdf_name(instance, filename):
    return f'pdfs/{filename}' 

class Producto(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    imagen = models.ImageField(upload_to='productos/', blank=True)
    precio = models.IntegerField(  
        validators=[MinValueValidator(1)],  
        help_text="Precio en pesos chilenos (sin decimales)"
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text="Cantidad disponible en inventario"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    pdf = models.FileField(upload_to='pdfs/', blank=True, null=True)  
    es_estatico = models.BooleanField(default=False) 

    def __str__(self):
        return f"{self.nombre} (${self.precio:,})".replace(",", ".")
    
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('CLIENT', 'Client'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='CLIENT')
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f'{self.user.username} - {self.role}'


# Señal para crear automáticamente el perfil cuando se crea un usuario
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance, role='CLIENT')

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        instance.userprofile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=instance, role='CLIENT')

class Carrito(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f'Carrito de {self.user.username}'
    
    def get_total(self):
        items = self.items.all()
        return sum(item.get_subtotal() for item in items)

class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    
    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
    
    def get_subtotal(self):
        return self.producto.precio * self.cantidad 
    
class Orden(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pendiente'),
        ('COMPLETED', 'Completada'),
        ('CANCELLED', 'Cancelada'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f'Orden {self.id} - {self.user.username}'

class OrdenItem(models.Model):
    orden = models.ForeignKey(Orden, related_name='items', on_delete=models.CASCADE)
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f'{self.cantidad} x {self.producto.nombre}'
    
    def get_subtotal(self):
        return self.precio_unitario * self.cantidad        
        
class ListaDeseos(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_agregado = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'producto']  # Evita duplicados
        verbose_name = "Lista de Deseos"
        verbose_name_plural = "Lista de Deseos"

    def __str__(self):
        return f'{self.user.username} - {self.producto.nombre}'