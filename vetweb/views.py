import os
from django.shortcuts import render, redirect, get_object_or_404
from .models import Producto
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponse,  Http404  , request
from django.template.loader import render_to_string
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from .forms import CustomUserCreationForm  # Añadimos esta importación
from functools import wraps
from .models import Producto, Carrito, CarritoItem, Orden, OrdenItem, UserProfile
from django.dispatch import receiver




def index(request):
    import os
    static_root = settings.STATIC_ROOT
    static_dirs = settings.STATICFILES_DIRS
    css_path = os.path.join(settings.BASE_DIR, 'vetweb', 'static', 'vetweb', 'css', 'style.css')
    print(f"STATIC_ROOT: {static_root}")
    print(f"STATICFILES_DIRS: {static_dirs}")
    print(f"CSS Path exists: {os.path.exists(css_path)}")
    print(f"Full CSS Path: {css_path}")
    return render(request, 'vetweb/index.html')

def lista_productos(request):
    productos = Producto.objects.all().order_by('id')
    
    # Filtros (mantén tu código actual)
    categoria_id = request.GET.get('categoria')
    if categoria_id:
        productos = productos.filter(categoria_id=categoria_id)
    
    min_precio = request.GET.get('min_precio')
    max_precio = request.GET.get('max_precio')
    if min_precio:
        productos = productos.filter(precio__gte=min_precio)
    if max_precio:
        productos = productos.filter(precio__lte=max_precio)
    
    busqueda = request.GET.get('buscar')
    if busqueda:
        productos = productos.filter(
            Q(nombre__icontains=busqueda) |
            Q(descripcion__icontains=busqueda)
        )
    context = {
        'productos': productos,
        'filtros_aplicados': any([categoria_id, min_precio, max_precio, busqueda])  # Nuevo
    }
    return render(request, 'vetweb/productos.html', context)
    
def quienes_somos(request):
    return render(request, 'vetweb/quienes_somos.html') 

def contacto(request):
    return render(request, 'vetweb/contacto.html')

def login_admin(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin:index')
        else:
            return render(request, 'vetweb/admin/login.html', {'error': 'Credenciales inválidas'})
    return render(request, 'vetweb/admin/login.html')

@login_required
def admin_dashboard(request):
    productos = Producto.objects.all()
    return render(request, 'vetweb/admin/dashboard.html', {'productos': productos})
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_active:
                login(request, user)
                
                # Obtener o crear el perfil
                try:
                    user_profile = UserProfile.objects.get(user=user)
                except UserProfile.DoesNotExist:
                    # Si no existe el perfil, lo creamos
                    user_profile = UserProfile.objects.create(user=user, role='CLIENT')
                
                messages.success(request, f'¡Bienvenido {username}!')
                
                # Redirigir según el rol
                if user_profile.role == 'ADMIN':
                    return redirect('vetweb:admin_dashboard')
                return redirect('vetweb:index')
            else:
                messages.error(request, 'Tu cuenta está desactivada.')
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'vetweb/auth/login.html')
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Cuenta creada exitosamente. Por favor revisa tu correo para activar tu cuenta.')
            return redirect('vetweb:login')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'vetweb/auth/register.html', {'form': form})

def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "¡Usuario registrado exitosamente! Puedes iniciar sesión ahora.")
            return redirect('login')  # Redirige al inicio de sesión
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('vetweb:index')

@login_required
def profile_view(request):
    return render(request, 'vetweb/cliente/perfil.html')


def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'vetweb/detalle_producto.html', {
        'producto': producto,
        'MEDIA_URL': settings.MEDIA_URL
    })
    
@login_required
def admin_dashboard(request):
    if request.user.userprofile.role != 'ADMIN':
        return redirect('vetweb:index')  # Redirigir si no es administrador
    productos = Producto.objects.all()
    return render(request, 'vetweb/admin/dashboard.html', {'productos': productos})    

def download_pdf(request , producto_id):
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        
        if producto.pdf:
            file_path = producto.pdf.path
            
            # Verifica si el archivo existe
            if os.path.exists(file_path):
                response = FileResponse(open(file_path, 'rb'))
                response['Content-Type'] = 'application/pdf'
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
            else:
                raise Http404("Archivo no encontrado")
        else:
            raise Http404("El PDF no está disponible para este producto")
    except Exception as e:
        raise Http404(f"Error al descargar el archivo: {str(e)}")
def product_manager_required(function):
    @wraps(function)
    def wrap(request, *args, **kwargs):
        if request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'PRODUCT_MANAGER':
            return function(request, *args, **kwargs)
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('vetweb:index')
    return wrap

@login_required
@product_manager_required
def productos_admin(request):
    productos = Producto.objects.all()
    return render(request, 'vetweb/productos/admin.html', {'productos': productos})

@login_required
@product_manager_required
def producto_crear(request):
    if request.method == 'POST':
        # Lógica para crear producto
        pass
    return render(request, 'vetweb/productos/crear.html')

# Vistas de Administración (CRUD)
@login_required
def admin_productos(request):
    if not request.user.userprofile.role == 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('vetweb:index')
        
    productos = Producto.objects.all()
    return render(request, 'vetweb/admin/productos.html', {'productos': productos})

@login_required
def admin_producto_crear(request):
    if not request.user.userprofile.role == 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('vetweb:index')
        
    if request.method == 'POST':
        # Procesar el formulario
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        precio = request.POST.get('precio')
        stock = request.POST.get('stock')
        imagen = request.FILES.get('imagen')
        
        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            imagen=imagen
        )
        messages.success(request, 'Producto creado exitosamente')
        return redirect('vetweb:admin_productos')
        
    return render(request, 'vetweb/admin/producto_crear.html')

@login_required
def admin_producto_editar(request, producto_id):
    if not request.user.userprofile.role == 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('vetweb:index')
        
    producto = get_object_or_404(Producto, id=producto_id)
    
    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre')
        producto.descripcion = request.POST.get('descripcion')
        producto.precio = request.POST.get('precio')
        producto.stock = request.POST.get('stock')
        
        if request.FILES.get('imagen'):
            producto.imagen = request.FILES.get('imagen')
            
        producto.save()
        messages.success(request, 'Producto actualizado exitosamente')
        return redirect('vetweb:admin_productos')
        
    return render(request, 'vetweb/admin/producto_editar.html', {'producto': producto})

@login_required
def admin_producto_eliminar(request, producto_id):
    if not request.user.userprofile.role == 'ADMIN':
        messages.error(request, 'No tienes permisos para acceder a esta sección')
        return redirect('vetweb:index')
        
    producto = get_object_or_404(Producto, id=producto_id)
    producto.delete()
    messages.success(request, 'Producto eliminado exitosamente')
    return redirect('vetweb:admin_productos')

# Vistas del Carrito
@login_required
@login_required
def carrito_ver(request):
    carrito, created = Carrito.objects.get_or_create(user=request.user)
    
    # Calculamos los valores directamente en la vista
    subtotal = int(carrito.get_total())
    iva = int(subtotal * 0.19)  # 19% de IVA
    total = int(subtotal * 1.19)
    
    context = {
        'carrito': carrito,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
    }
    return render(request, 'vetweb/cliente/carrito.html', context)

@login_required
def carrito_agregar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, created = Carrito.objects.get_or_create(user=request.user)
    
    # Verificar si el producto ya está en el carrito
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

# Vista del historial de compras
@login_required
def historial_compras(request):
    ordenes = Orden.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'vetweb/cliente/historial.html', {'ordenes': ordenes})

@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    if created:
        Carrito.objects.create(user=instance)