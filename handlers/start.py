"""
Handler de inicio — detecta si el usuario es chofer o cliente
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_chofer, get_cliente, registrar_cliente


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    # Ver si ya está registrado como chofer
    chofer = get_chofer(telegram_id)
    if chofer:
        estado = chofer['estado']
        if estado == 'activo':
            await update.message.reply_text(
                f"👋 Bienvenido de nuevo, *{chofer['nombre']}*\n\n"
                f"✅ Tu cuenta está activa.\n"
                f"🚗 Vehículo: {chofer['vehiculo']}\n"
                f"📍 Zona: {chofer['municipio']}, {chofer['provincia']}\n"
                f"⭐ Valoración: {chofer['rating']}/5.0\n\n"
                f"Estás suscrito al canal de tu provincia. Los viajes llegarán allí.",
                
            )
        elif estado == 'pendiente':
            await update.message.reply_text(
                "⏳ Tu registro está *pendiente de aprobación*.\n\n"
                "El administrador revisará tu solicitud pronto. "
                "Te avisaremos cuando tu cuenta esté activa.",
                
            )
        elif estado == 'suspendido':
            await update.message.reply_text(
                "⛔ Tu cuenta está *suspendida*.\n\n"
                "Esto puede ser por cuota vencida. Escribe /pagar para renovar.",
                
            )
        return

    # Ver si ya está registrado como cliente
    cliente = get_cliente(telegram_id)
    if cliente:
        await update.message.reply_text(
            f"👋 Bienvenido de nuevo!\n\n"
            f"Para pedir un taxi escribe /viaje\n"
            f"Para ver tu perfil escribe /perfil",
            
        )
        return

    # Usuario nuevo — preguntar rol
    keyboard = [
        [InlineKeyboardButton("🚗 Soy Chofer", callback_data="rol_chofer")],
        [InlineKeyboardButton("🙋 Soy Cliente", callback_data="rol_cliente")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🚖 *Bienvenido a TaxiCuba Bot*\n\n"
        "El sistema de transporte privado más fácil de Cuba.\n\n"
        "¿Cómo quieres registrarte?",
        reply_markup=reply_markup,
        
    )
