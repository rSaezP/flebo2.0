from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from .models import Producto, Carrito, CarritoItem

def lista_productos(request):
    productos = Producto.objects.all()  
    return render(request, 'vetweb/productos.html', {'productos': productos})

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    context = {
        'producto': producto,
        'page_type': 'detalle_producto',  
        'MEDIA_URL': settings.MEDIA_URL
    }
    
    return render(request, 'vetweb/detalle_producto.html', context)

@login_required
def carrito_ver(request):
    carrito, created = Carrito.objects.get_or_create(user=request.user)
    return render(request, 'vetweb/cliente/carrito.html', {'carrito': carrito})

@login_required
def carrito_agregar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, created = Carrito.objects.get_or_create(user=request.user)
    
    carrito_item, created = CarritoItem.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': 1}
    )
    
    if not created:
        carrito_item.cantidad += 1
        carrito_item.save()
    
    messages.success(request, 'Producto agregado al carrito')
    return redirect('vetweb:carrito_ver')

@login_required
def carrito_eliminar(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id, carrito__user=request.user)
    item.delete()
    messages.success(request, 'Producto eliminado del carrito')
    return redirect('vetweb:carrito_ver')

# Create your views here.
