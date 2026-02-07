import firebase_service
import sys

# Datos de prueba con email de cliente
# USANDO EL MISMO EMAIL QUE EL ADMIN PARA QUE EL USUARIO PUEDA VERLO EN SU BANDEJA
# (O el usuario puede cambiarlo si quiere probar otro)
test_doc = {
    "nombre": "CLIENTE DE PRUEBA",
    "fecha": "2026-02-01",
    "hora": "14:00",
    "telefono": "666-777-888",
    "servicio": "Corte y Barba",
    "email": "dg960062@gmail.com" # Usamos el mismo del emisor O el del admin para probar
}

print("Iniciando prueba de DOBLE envío (Admin + Cliente)...")
print(f"Datos: {test_doc}")

try:
    service = firebase_service.FirebaseService("dummy.json")
    
    # Sobreescribimos la función interna para ver qué está pasando si falla
    # Pero mejor llamamos directamente a la función real
    service.send_email_notification(test_doc)
    
    print("--- Ejecución finalizada ---")
except Exception as e:
    print(f"FATAL ERROR: {e}")
