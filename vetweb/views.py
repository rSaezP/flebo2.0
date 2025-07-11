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
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.core.mail import send_mail 
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .functions import generateAccessToken, createOrder





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

def obtener_carrito_de_usuario(usuario):
    """Función centralizada para obtener o crear el carrito de un usuario"""
    try:
        carrito = Carrito.objects.get(user=usuario)
    except Carrito.DoesNotExist:
        carrito = Carrito.objects.create(user=usuario)
    return carrito
    
def quienes_somos(request):
    return render(request, 'vetweb/quienes_somos.html') 

def contacto(request):
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            email = request.POST.get('email')
            asunto = request.POST.get('asunto')
            telefono = request.POST.get('telefono')  # Nuevo campo
            mensaje = request.POST.get('mensaje')
           
            
            mensaje_completo = f"""
            Nuevo mensaje de contacto:
            
            Nombre: {nombre}
            Email: {email}
            Asunto: {asunto}
            Teléfono: {telefono}
            Mensaje: {mensaje}
            
            """
            
            send_mail(
                subject=f'Nuevo contacto: {asunto}',
                message=mensaje_completo,
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            
            messages.success(request, '¡Gracias por contactarnos! Hemos recibido tu mensaje. Nuestro equipo se pondrá en contacto contigo lo antes posible.')
            return HttpResponseRedirect(reverse('vetweb:contacto') + '#')  # Agregamos # al final
            
        except Exception as e:
            messages.error(request, 'Error al enviar el mensaje. Por favor, intenta nuevamente.')
    
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
def download_pdf(request, producto_id):
    try:
        producto = get_object_or_404(Producto, id=producto_id)
        
        if not producto.pdf:
            raise Http404("PDF no disponible para este producto")
        
        # Verificar que el archivo existe físicamente
        if not os.path.exists(producto.pdf.path):
            raise Http404("Archivo PDF no encontrado en el servidor")
        
        # Obtener el nombre del archivo
        filename = os.path.basename(producto.pdf.name)
        
        # Crear respuesta con el archivo
        response = FileResponse(
            open(producto.pdf.path, 'rb'),
            content_type='application/pdf'
        )
        
        # Configurar headers para descarga
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        return response
        
    except Exception as e:
        raise Http404(f"Error al descargar el archivo: {str(e)}")

def detalle_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    
    # Verificar si el producto está en la lista de deseos del usuario
    en_lista_deseos = False
    if request.user.is_authenticated:
        en_lista_deseos = ListaDeseos.objects.filter(
            user=request.user, 
            producto=producto
        ).exists()
    
    context = {
        'producto': producto,
        'en_lista_deseos': en_lista_deseos,
    }
    
    return render(request, 'vetweb/detalle_producto.html', context)




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
    carrito = obtener_carrito_de_usuario(request.user)
    
    # Calculamos los valores directamente en la vista
    subtotal = carrito.get_subtotal()
    iva = carrito.get_iva()  # 19% de IVA
    total = carrito.get_total()
    
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
    carrito = obtener_carrito_de_usuario(request.user)
    
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
    
    # Obtener los items de cada orden para mostrar los productos
    for orden in ordenes:
        orden.items_detalle = OrdenItem.objects.filter(orden=orden).select_related('producto')
    
    context = {
        'ordenes': ordenes,
    }
    return render(request, 'vetweb/cliente/historial.html', context)

@receiver(post_save, sender=User)
def create_user_cart(sender, instance, created, **kwargs):
    """Crear carrito automáticamente cuando se crea un usuario"""
    if created:
        try:
            Carrito.objects.create(user=instance)
        except Exception as e:
            # Si hay algún error, no hacer nada para evitar conflictos
            pass
        
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

@login_required
def checkout(request):
    carrito = obtener_carrito_de_usuario(request.user)
    
    # Validar si el carrito está vacío
    if not carrito.items.exists():
        return redirect('vetweb:carrito_ver')  # Redirige si no hay items
    
    # Calcular totales (como ya lo haces en carrito_ver)
    subtotal = carrito.get_subtotal()
    iva = carrito.get_iva()
    total = carrito.get_total()
    
    context = {
        'carrito': carrito,
        'subtotal': subtotal,
        'iva': iva,
        'total': total,
        # Agrega más datos si es necesario (ej: direcciones de envío)
    }
    return render(request, 'vetweb/cliente/checkout.html', context)

@login_required
def crear_orden(request):
    if request.method == 'POST':
        try:
            carrito = obtener_carrito_de_usuario(request.user)
            
            if not carrito.items.exists():
                messages.error(request, 'Tu carrito está vacío')
                return redirect('vetweb:carrito_ver')
            
            # Calcular total (por si acaso no está cacheado)
            total = carrito.get_total()
            
            # Crear la orden
            orden = Orden.objects.create(
                user=request.user, 
                total=total,
                status='PENDING'  # Asegurar estado inicial
            )
            
            # Crear items de la orden
            for item in carrito.items.all():
                OrdenItem.objects.create(
                    orden=orden,
                    producto=item.producto,
                    cantidad=item.cantidad,
                    precio_unitario=item.producto.precio  # Usar precio_unitario en lugar de subtotal
                )
            
            # Limpiar el carrito
            carrito.items.all().delete()
            
            # Redirigir a confirmación de esta orden específica
            return redirect('vetweb:confirmacion_orden', orden_id=orden.id)
            
        except Exception as e:
            # logger.error(f"Error al crear orden: {str(e)}")
            messages.error(request, 'Ocurrió un error al procesar tu orden')
            return redirect('vetweb:carrito_ver')
    
    # Si no es POST, redirigir al carrito
    return redirect('vetweb:carrito_ver')

@login_required
def confirmacion_orden(request, orden_id):
    orden = get_object_or_404(Orden, id=orden_id, user=request.user)
    return render(request, 'vetweb/cliente/confirmacion_orden.html', {'orden': orden})

def policies_view(request):
    return render(request, 'vetweb/policies.html')

#view para crear orden con PayPal
class CrearOrden(APIView):
    def post(self, request):
        orden = createOrder('productos')
        return Response(orden, status=status.HTTP_200_OK)

def limpiar_carritos_huérfanos():
    """Función para limpiar carritos sin usuario o items sin carrito"""
    try:
        # Eliminar carritos sin usuario
        carritos_sin_usuario = Carrito.objects.filter(user__isnull=True)
        carritos_sin_usuario.delete()
        
        # Eliminar items sin carrito
        items_sin_carrito = CarritoItem.objects.filter(carrito__isnull=True)
        items_sin_carrito.delete()
        
        return True
    except Exception as e:
        return False

@login_required
def diagnosticar_carrito(request):
    """Vista de diagnóstico para verificar el estado del carrito del usuario"""
    usuario = request.user
    
    # Verificar si el usuario tiene carrito
    try:
        carrito = Carrito.objects.get(user=usuario)
        carrito_existe = True
    except Carrito.DoesNotExist:
        carrito_existe = False
        carrito = None
    
    # Verificar items del carrito
    if carrito:
        items_count = carrito.items.count()
        items_detalle = list(carrito.items.all().values('id', 'producto__nombre', 'cantidad'))
    else:
        items_count = 0
        items_detalle = []
    
    # Intentar crear carrito si no existe
    if not carrito_existe:
        try:
            carrito = Carrito.objects.create(user=usuario)
            carrito_creado = True
        except Exception as e:
            carrito_creado = False
            error = str(e)
    else:
        carrito_creado = False
        error = None
    
    # Limpiar carritos huérfanos
    limpieza_exitosa = limpiar_carritos_huérfanos()
    
    context = {
        'usuario': usuario.username,
        'carrito_existe': carrito_existe,
        'carrito_creado': carrito_creado,
        'items_count': items_count,
        'items_detalle': items_detalle,
        'limpieza_exitosa': limpieza_exitosa,
        'error': error if 'error' in locals() else None,
    }
    
    return render(request, 'vetweb/cliente/diagnostico_carrito.html', context)