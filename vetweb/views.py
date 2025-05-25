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
from django.http import JsonResponse
from .models import ListaDeseos
from .decorators import admin_required
from django.db.models import Count
from django.http import HttpResponse
from django.contrib.auth.models import User




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
    
    # Obtener lista de productos en deseos para el usuario actual
    productos_en_deseos = []
    if request.user.is_authenticated:
        productos_en_deseos = ListaDeseos.objects.filter(user=request.user).values_list('producto_id', flat=True)
    
    context = {
        'productos': productos,
        'productos_en_deseos': productos_en_deseos,
        'filtros_aplicados': any([categoria_id, min_precio, max_precio, busqueda])
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




def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'vetweb/detalle_producto.html', {
        'producto': producto,
        'MEDIA_URL': settings.MEDIA_URL
    })
    


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
    """Agregar un producto al carrito"""
    if request.method != 'POST':
        return redirect('vetweb:productos')
    
    producto = get_object_or_404(Producto, id=producto_id)
    carrito, created = Carrito.objects.get_or_create(user=request.user)
    
    # Verificar si el producto ya está en el carrito
    carrito_item, item_created = CarritoItem.objects.get_or_create(
        carrito=carrito,
        producto=producto,
        defaults={'cantidad': 1}
    )
    
    if not item_created:
        carrito_item.cantidad += 1
        carrito_item.save()
    
    # Mensaje de éxito normal (para redirecciones)
    messages.success(request, f"{producto.nombre} agregado al carrito")
    
    # Si es una solicitud AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'items_count': carrito.items.count(),
            'message': f"{producto.nombre} agregado al carrito"
        })
    
    # Redirección normal
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
        
@login_required
def agregar_a_deseos(request, producto_id):
    """Agregar o quitar un producto de la lista de deseos"""
    if request.method != 'POST':
        return redirect('vetweb:productos')
    
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Verificar si ya existe en la lista de deseos
    deseo_existente = ListaDeseos.objects.filter(user=request.user, producto=producto).first()
    
    if deseo_existente:
        # Si ya existe, lo quitamos
        deseo_existente.delete()
        in_wishlist = False
        mensaje = f"{producto.nombre} eliminado de tu lista de deseos."
    else:
        # Si no existe, lo agregamos
        ListaDeseos.objects.create(user=request.user, producto=producto)
        in_wishlist = True
        mensaje = f"{producto.nombre} agregado a tu lista de deseos."
    
    # Mensaje de éxito normal (para redirecciones)
    messages.success(request, mensaje)
    
    # Si es una solicitud AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'message': mensaje
        })
    
    # Redirección normal
    return redirect(request.META.get('HTTP_REFERER', 'vetweb:productos'))
    
@login_required
def lista_deseos_view(request):
    deseos = ListaDeseos.objects.filter(user=request.user)
    return render(request, 'vetweb/cliente/lista_deseos.html', {
        'deseos': deseos
    })

@login_required
def quitar_de_deseos(request, producto_id):
    if request.method == 'POST':
        ListaDeseos.objects.filter(
            user=request.user,
            producto_id=producto_id
        ).delete()
        messages.success(request, 'Producto eliminado de tu lista de deseos')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Producto eliminado de tu lista de deseos'
            })
        
        return redirect('vetweb:lista_deseos_view')
    return redirect('vetweb:lista_deseos_view')

@login_required
def profile_view(request):
    """Vista del perfil de usuario con lista de deseos e historial de compras"""
    # Obtenemos o creamos el perfil del usuario
    try:
        user_profile = request.user.userprofile
    except UserProfile.DoesNotExist:
        user_profile = UserProfile.objects.create(user=request.user, role='CLIENT')
    
    # Obtener lista de deseos
    lista_deseos = ListaDeseos.objects.filter(user=request.user).select_related('producto')
    
    # Obtener historial de compras (ajusta el campo si es necesario)
    try:
        ordenes = Orden.objects.filter(user=request.user).order_by('-created_at')
    except:
        try:
            # Intenta con otro nombre de campo si created_at no existe
            ordenes = Orden.objects.filter(user=request.user).order_by('-fecha_creacion')
        except:
            # Si todo falla, al menos devolver algo
            ordenes = Orden.objects.filter(user=request.user)
    
    # Procesar actualización de perfil
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            request.user.email = email
            request.user.save()
            messages.success(request, 'Perfil actualizado exitosamente')
        return redirect('vetweb:profile')
    
    context = {
        'user_profile': user_profile,
        'lista_deseos': lista_deseos,
        'ordenes': ordenes,
    }
    
    return render(request, 'vetweb/cliente/perfil.html', context)

@admin_required
def admin_dashboard(request):
    total_productos = Producto.objects.count()
    productos_sin_stock = Producto.objects.filter(stock=0).count()
    ultimos_productos = Producto.objects.order_by('-fecha_creacion')[:5]
    
    context = {
        'total_productos': total_productos,
        'productos_sin_stock': productos_sin_stock,
        'ultimos_productos': ultimos_productos,
    }
    
    return render(request, 'vetweb/admin/dashboard.html', context)

@admin_required
def admin_productos(request):
    productos = Producto.objects.all().order_by('-fecha_creacion')
    return render(request, 'vetweb/admin/productos_admin.html', {'productos': productos})

@admin_required
def admin_producto_crear(request):
    if request.method == 'POST':
        try:
            # Crear el producto con los datos del formulario
            producto = Producto.objects.create(
                nombre=request.POST.get('nombre'),
                descripcion=request.POST.get('descripcion'),
                precio=request.POST.get('precio', 0),
                stock=request.POST.get('stock', 0)
            )
            
            # Manejar la imagen si se proporcionó una
            if 'imagen' in request.FILES:
                producto.imagen = request.FILES['imagen']
            
            # Manejar el PDF si se proporcionó uno
            if 'pdf' in request.FILES:
                producto.pdf = request.FILES['pdf']
                
            producto.save()
            
            messages.success(request, 'Producto creado exitosamente')
            return redirect('vetweb:admin_productos')
        except Exception as e:
            messages.error(request, f'Error al crear el producto: {str(e)}')
            
    return render(request, 'vetweb/admin/producto_form.html', {
        'producto': None
    })

@admin_required
def admin_producto_editar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == 'POST':
        try:
            producto.nombre = request.POST.get('nombre')
            producto.descripcion = request.POST.get('descripcion')
            producto.precio = request.POST.get('precio', 0)
            producto.stock = request.POST.get('stock', 0)
            
            if 'imagen' in request.FILES:
                producto.imagen = request.FILES['imagen']
            if 'pdf' in request.FILES:
                producto.pdf = request.FILES['pdf']
                
            producto.save()
            messages.success(request, 'Producto actualizado exitosamente')
            return redirect('vetweb:admin_productos')
        except Exception as e:
            messages.error(request, f'Error al actualizar el producto: {str(e)}')
    return render(request, 'vetweb/admin/producto_form.html', {'producto': producto})

@admin_required
def admin_producto_eliminar(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    try:
        producto.delete()
        messages.success(request, 'Producto eliminado exitosamente')
    except Exception as e:
        messages.error(request, f'Error al eliminar el producto: {str(e)}')
    return redirect('vetweb:admin_productos')