"""
Configuración de TaxiCuba Bot
IMPORTANTE: Edita este archivo con tus datos reales antes de subir el bot
"""

import os

# ─────────────────────────────────────────────────────────────
# TU ID DE ADMINISTRADOR EN TELEGRAM
# Para saber tu ID: escríbele a @userinfobot en Telegram
# ─────────────────────────────────────────────────────────────
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# ─────────────────────────────────────────────────────────────
# INFORMACIÓN DE PAGO (que ven los choferes al escribir /pagar)
# ─────────────────────────────────────────────────────────────
INFO_PAGO = """
💳 *Instrucciones de Pago — Cuota Mensual: 250 CUP*

Puedes pagar por:
• *Transfermóvil:* 9205069991089805
• *EnZona:* 9205069991089805

Después de pagar:
1. Toma foto del comprobante
2. Envíala aquí mismo en el chat
3. El admin confirmará en menos de 24 horas

¿Dudas? Escribe al admin: @yoanosiel_98
"""

# ─────────────────────────────────────────────────────────────
# REGLAS DEL SISTEMA
# ─────────────────────────────────────────────────────────────
PRECIO_MINIMO_CUP = 50          # Precio mínimo que puede ofrecer un cliente
CUOTA_MENSUAL_CUP = 250         # Cuota mensual de los choferes
MINUTOS_EXPIRACION_VIAJE = 30   # Minutos antes de que un viaje expire sin chofer
DIAS_AVISO_CUOTA = 3            # Días antes del vencimiento para avisar al chofer
