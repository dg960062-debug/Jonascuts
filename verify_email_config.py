import firebase_service
import os

# Dummy data
test_doc = {
    "nombre": "PRUEBA SISTEMA",
    "fecha": "2026-02-01",
    "hora": "12:00",
    "telefono": "000-000-000",
    "servicio": "Test de Correo"
}

print("Iniciando prueba de correo...")
try:
    # Use relative path to credentials if needed, but we just need the class
    # The Send Email method doesn't use Firebase connection so cred path doesn't matter for this test
    service = firebase_service.FirebaseService("dummy_path.json")
    
    # Call the method directly
    service.send_email_notification(test_doc)
    print("Prueba finalizada. Revisa tu bandeja de entrada.")
except Exception as e:
    print(f"Error durante la prueba: {e}")
