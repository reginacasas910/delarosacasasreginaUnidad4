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
import stripe
import uuid
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponse

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
            producto = Producto.objects.get(id=int(producto_id))
        except (Producto.DoesNotExist, ValueError):
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

    carrito[producto_id] = int(carrito.get(producto_id, 0)) + 1

    request.session['carrito'] = carrito
    request.session.modified = True

    return redirect('carrito')

@usuario_requerido
@require_POST
def actualizar_carrito(request, producto_id):

    carrito = request.session.get('carrito', {})

    producto_id = str(producto_id)

    if producto_id in carrito:
        try:
            cantidad = int(request.POST.get('cantidad', 1))

            if cantidad <= 0:
                carrito.pop(producto_id)
            elif cantidad <= 99:
                carrito[producto_id] = cantidad

        except (ValueError, TypeError):
            pass

    request.session['carrito'] = carrito
    request.session.modified = True

    return redirect('carrito')

@usuario_requerido
@require_POST
def eliminar_del_carrito(request, producto_id):

    carrito = request.session.get('carrito', {})

    carrito.pop(str(producto_id), None)

    request.session['carrito'] = carrito
    request.session.modified = True

    return redirect('carrito')

@usuario_requerido
@require_POST
def crear_pago(request):

    stripe.api_key = settings.STRIPE_SECRET_KEY

    if not stripe.api_key:
        return HttpResponse(
            "No se ha configurado la clave de Stripe.",
            status=500
        )

    carrito = request.session.get('carrito', {})

    if not carrito:
        return redirect('carrito')

    line_items = []

    try:
        for producto_id, cantidad in carrito.items():

            producto = get_object_or_404(
                Producto,
                id=int(producto_id)
            )

            cantidad = int(cantidad)

            if cantidad < 1 or cantidad > 99:
                return HttpResponse("Cantidad no válida.", status=400)

            precio_centavos = int(
                (producto.precio * 100).quantize(Decimal('1'))
            )

            line_items.append({
                'price_data': {
                    'currency': settings.STRIPE_CURRENCY,
                    'product_data': {
                        'name': producto.nombre,
                        'description': producto.descripcion[:500],
                    },
                    'unit_amount': precio_centavos,
                },
                'quantity': cantidad,
            })

        sesion = stripe.checkout.Session.create(
            line_items=line_items,
            mode='payment',
            success_url=request.build_absolute_uri(
                reverse('pago_exitoso')
            ) + '?session_id={CHECKOUT_SESSION_ID}',

            cancel_url=request.build_absolute_uri(
                reverse('pago_cancelado')
            ),

            metadata={
                'usuario_id': str(request.session['usuario_id'])
            }
        )

        return redirect(sesion.url, permanent=False)

    except stripe.error.StripeError as error:
        return HttpResponse(
            "No fue posible iniciar el pago: " + str(error),
            status=400
        )
    except (ValueError, TypeError):
        return HttpResponse(
            "Los datos del carrito no son válidos.",
            status=400
        )


@usuario_requerido
def pago_exitoso(request):

    session_id = request.GET.get('session_id')

    if not session_id:
        return redirect('carrito')

    stripe.api_key = settings.STRIPE_SECRET_KEY

    try:
        sesion = stripe.checkout.Session.retrieve(session_id)

        if (
            sesion.payment_status == 'paid'
            and sesion.metadata.get('usuario_id')
            == str(request.session['usuario_id'])
        ):
            request.session['carrito'] = {}
            request.session.modified = True

            return render(request, 'pago_exitoso.html')

        return HttpResponse(
            "El pago todavía no ha sido confirmado.",
            status=400
        )

    except stripe.error.StripeError:
        return HttpResponse(
            "No se pudo verificar el pago.",
            status=400
        )

@usuario_requerido
def pago_cancelado(request):
    return render(request, 'pago_cancelado.html')