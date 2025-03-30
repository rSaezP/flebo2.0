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