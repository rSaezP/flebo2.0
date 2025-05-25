from django.shortcuts import redirect
from functools import wraps

def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Verificar si el usuario está autenticado y es staff o tiene rol de ADMIN
        if not request.user.is_authenticated:
            return redirect('vetweb:login')
        
        # Verificar si es staff o tiene rol ADMIN en su perfil
        if request.user.is_staff or (hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'ADMIN'):
            return view_func(request, *args, **kwargs)
        else:
            # Redireccionar a la página principal si no tiene permisos
            return redirect('vetweb:index')
    return _wrapped_view