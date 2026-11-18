from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from functools import wraps
from .models import Producto, Usuario, Contacto
from .serializers import ProductoSerializer
from django.views.decorators.http import require_POST
from decimal import Decimal

@api_view(['GET'])
def api_productos(request):
    productos = Producto.objects.all()
    serializer = ProductoSerializer(productos, many=True)

    return Response(serializer.data)


@api_view(['GET'])
def api_producto_detalle(request, id):
    try:
        producto = Producto.objects.get(id=id)
    except Producto.DoesNotExist:
        return Response(
            {'error': 'Producto no encontrado'},
            status=404
        )

    serializer = ProductoSerializer(producto)

    return Response(serializer.data)

# Create your views here.
def usuario_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get("usuario_id"):
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper

def inicio(request):
    productos = Producto.objects.all()

    return render(request, 'inicio.html', {
        'productos': productos
    })

def maquillaje(request):
    productos = Producto.objects.all()

    return render(request, 'maquillaje.html', {
        'productos': productos
    })

@usuario_requerido
def buscar(request):
    termino = request.GET.get('q', '')

    if termino:
        productos = Producto.objects.filter(
            nombre__icontains=termino
        )
    else:
        productos = Producto.objects.all()

    return render(request, 'buscar.html', {
        'productos': productos,
        'termino': termino
    })

def contacto(request):
    mensaje_exito = None
    error = None

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        correo = request.POST.get("correo")
        mensaje = request.POST.get("mensaje")

        if nombre and correo and mensaje:
            Contacto.objects.create(
                nombre=nombre,
                correo=correo,
                mensaje=mensaje
            )
            mensaje_exito = "Mensaje enviado correctamente"
        else:
            error = "Todos los campos son obligatorios"

    return render(request, "contacto.html", {
        "mensaje_exito": mensaje_exito,
        "error": error
    })

def ayuda(request):
    return render(request, 'ayuda.html')

def registro(request):

    if request.method == 'POST':

        nombre = request.POST['nombre']
        correo = request.POST['correo']
        contraseña = request.POST['contraseña']

        Usuario.objects.create(
            nombre=nombre,
            correo=correo,
            contraseña=make_password(contraseña)
        )

        return redirect('inicio')

    return render(request, 'registro.html')

def login_view(request):
    error = None

    if request.method == "POST":
        nombre = request.POST.get("nombre")
        contraseña = request.POST.get("contraseña")

        try:
            usuario = Usuario.objects.get(nombre=nombre)

            contraseña_valida = check_password(
                contraseña, usuario.contraseña
            )

            # Compatibilidad con contraseñas antiguas sin hash
            if not contraseña_valida and usuario.contraseña == contraseña:
                contraseña_valida = True
                usuario.contraseña = make_password(contraseña)
                usuario.save()

            if contraseña_valida:
                request.session["usuario_id"] = usuario.id
                request.session["usuario_nombre"] = usuario.nombre

                return redirect("buscar")
            else:
                error = "Contraseña incorrecta"

        except Usuario.DoesNotExist:
            error = "El usuario no existe"

    return render(request, "login.html", {"error": error})

def recuperar(request):
        mensaje = None
        error = None

        if request.method == "POST":
            nombre = request.POST.get("nombre")
            correo = request.POST.get("correo")
            contraseña_actual = request.POST.get("contraseña_actual")
            nueva_contraseña = request.POST.get("nueva_contraseña")

            try:
                usuario = Usuario.objects.get(nombre=nombre, correo=correo)

                # validar contraseña actual
                if usuario.contraseña == contraseña_actual:
                    usuario.contraseña = nueva_contraseña
                    usuario.save()

                    mensaje = "Contraseña actualizada correctamente"
                else:
                    error = "La contraseña actual no es correcta"

            except Usuario.DoesNotExist:
                error = "Usuario no encontrado"

        return render(request, "recuperar.html", {
            "mensaje": mensaje,
            "error": error
        })

def mapa_sitio(request):
    return render(request, 'mapa_sitio.html')

def logout_view(request):
    request.session.flush()
    return redirect('/')

@usuario_requerido
def carrito(request):
    carrito_session = request.session.get('carrito', {})

    productos_carrito = []
    total = Decimal('0.00')

    for producto_id, cantidad in carrito_session.items():

        try:
            producto = Producto.objects.get(id=producto_id)
        except Producto.DoesNotExist:
            continue

        subtotal = producto.precio * cantidad

        productos_carrito.append({
            'producto': producto,
            'cantidad': cantidad,
            'subtotal': subtotal
        })

        total += subtotal

    return render(request, 'carrito.html', {
        'productos_carrito': productos_carrito,
        'total': total
    })


@usuario_requerido
@require_POST
def agregar_al_carrito(request, producto_id):

    producto = get_object_or_404(Producto, id=producto_id)

    carrito = request.session.get('carrito', {})

    producto_id = str(producto.id)

    carrito[producto_id] = carrito.get(producto_id, 0) + 1

    request.session['carrito'] = carrito

    return redirect('carrito')


@usuario_requerido
@require_POST
def eliminar_del_carrito(request, producto_id):

    carrito = request.session.get('carrito', {})

    carrito.pop(str(producto_id), None)

    request.session['carrito'] = carrito

    return redirect('carrito')
