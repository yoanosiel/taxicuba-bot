"""
Handler de perfil de usuario
"""

from telegram import Update
from telegram.ext import ContextTypes
from database import get_chofer, get_cliente


async def perfil_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    chofer = get_chofer(user_id)
    if chofer:
        estado_emoji = {"activo": "✅", "pendiente": "⏳", "suspendido": "⛔"}.get(chofer['estado'], "❓")
        rating_stars = "⭐" * round(chofer['rating']) if chofer['rating'] > 0 else "Sin valoraciones"

        await update.message.reply_text(
            f"🚗 *Tu Perfil de Chofer*\n\n"
            f"👤 Nombre: {chofer['nombre']}\n"
            f"📞 Teléfono: {chofer['telefono']}\n"
            f"📍 Zona: {chofer['municipio']}, {chofer['provincia']}\n"
            f"🚗 Vehículo: {chofer['vehiculo']}\n"
            f"Estado: {estado_emoji} {chofer['estado'].capitalize()}\n"
            f"⭐ Valoración: {chofer['rating']}/5.0 ({rating_stars})\n"
            f"🚖 Viajes realizados: {chofer['viajes_total']}\n"
            f"📅 Último pago: {chofer['fecha_pago'] or 'No registrado'}\n\n"
            f"_Para renovar tu cuota escribe /pagar_",
            parse_mode="Markdown"
        )
        return

    cliente = get_cliente(user_id)
    if cliente:
        await update.message.reply_text(
            f"🙋 *Tu Perfil de Cliente*\n\n"
            f"📞 Teléfono: {cliente['telefono'] or 'No registrado'}\n"
            f"📍 Provincia habitual: {cliente['provincia'] or 'No registrada'}\n"
            f"⭐ Valoración: {cliente['rating']}/5.0\n"
            f"🚖 Viajes realizados: {cliente['viajes_total']}\n\n"
            f"_Para pedir un taxi escribe /viaje_",
            parse_mode="Markdown"
        )
        return

    await update.message.reply_text(
        "No tienes perfil aún. Escribe /start para registrarte."
    )
