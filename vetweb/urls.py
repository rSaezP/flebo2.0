from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'vetweb'

urlpatterns = [
    path('', views.index, name='index'),
    path('productos/', views.lista_productos, name='productos'),
    path('quienes-somos/', views.quienes_somos, name='quienes_somos'),
    path('contacto/', views.contacto, name='contacto'),
    path('admin/login/', views.login_admin, name='admin_login'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('auth/login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('producto/<int:producto_id>/', views.detalle_producto, name='detalle_producto'),
    path('download/pdf/<int:producto_id>/', views.download_pdf, name='download_pdf'),
    
# URLs para reseteo de contraseña con tus nombres de archivo
    # Password Reset URLs
   path('password_reset/',
    auth_views.PasswordResetView.as_view(
        template_name='vetweb/auth/password_reset_form.html',
        email_template_name='vetweb/auth/password_reset_email.html',  # Actualiza esta ruta
        success_url='/password_reset/done/'
    ),
    name='password_reset'),
    
    path('password_reset/done/', 
        auth_views.PasswordResetDoneView.as_view(
            template_name='vetweb/auth/password_reset_done.html'
        ), 
        name='password_reset_done'),
    
    path('reset/<uidb64>/<token>/',
    auth_views.PasswordResetConfirmView.as_view(
        template_name='vetweb/auth/password_reset_confirm.html',
        success_url='/password_reset/complete/'
        
    ),
    name='password_reset_confirm'),      

path('password_reset/complete/',  # Cambié 'reset/done' por 'password_reset/complete'          
    auth_views.PasswordResetCompleteView.as_view(             
        template_name='vetweb/auth/password_reset_complete.html'         
    ),         
    name='password_reset_complete'),

        # URLs de administración
    path('admin/productos/', views.admin_productos, name='admin_productos'),
    path('admin/productos/crear/', views.admin_producto_crear, name='admin_producto_crear'),
    path('admin/productos/<int:producto_id>/editar/', views.admin_producto_editar, name='admin_producto_editar'),
    path('admin/productos/<int:producto_id>/eliminar/', views.admin_producto_eliminar, name='admin_producto_eliminar'),
    
    # URLs del carrito
    path('carrito/', views.carrito_ver, name='carrito_ver'),
    path('carrito/agregar/<int:producto_id>/', views.carrito_agregar, name='carrito_agregar'),
    path('carrito/eliminar/<int:item_id>/', views.carrito_eliminar, name='carrito_eliminar'),
    
    # URLs del cliente
    path('mi-cuenta/historial/', views.historial_compras, name='historial_compras'),
]


