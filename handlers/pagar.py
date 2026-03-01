"""
Handler de pago de cuota
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_chofer
from config import INFO_PAGO, ADMIN_ID


async def pagar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chofer = get_chofer(user_id)

    if not chofer:
        await update.message.reply_text(
            "❌ Este comando es solo para choferes registrados.\n"
            "Escribe /start para registrarte."
        )
        return

    await update.message.reply_text(
        INFO_PAGO,
        parse_mode="Markdown"
    )
    await update.message.reply_text(
        "📸 Ahora envía la *foto del comprobante* de pago en este mismo chat.\n"
        "El admin la recibirá y confirmará tu pago.",
        parse_mode="Markdown"
    )

    # Guardar estado para recibir la foto
    context.user_data['esperando_comprobante'] = True


async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Recibe foto de comprobante y la reenvía al admin"""
    if not context.user_data.get('esperando_comprobante'):
        return

    user = update.effective_user
    chofer = get_chofer(user.id)

    if not chofer:
        return

    context.user_data['esperando_comprobante'] = False

    keyboard = [[InlineKeyboardButton("✅ Confirmar Pago", callback_data=f"admin_pago_{user.id}")]]

    if update.message.photo:
        await context.bot.send_photo(
            ADMIN_ID,
            update.message.photo[-1].file_id,
            caption=(
                f"💳 *Comprobante de pago recibido*\n\n"
                f"👤 Chofer: {chofer['nombre']}\n"
                f"📞 Tel: {chofer['telefono']}\n"
                f"📍 {chofer['municipio']}, {chofer['provincia']}\n"
                f"🔗 @{user.username or 'sin_usuario'} (ID: {user.id})"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    else:
        await context.bot.send_message(
            ADMIN_ID,
            f"💳 *Pago reportado (sin imagen)*\n\n"
            f"👤 Chofer: {chofer['nombre']}\n"
            f"📞 Tel: {chofer['telefono']}\n"
            f"📍 {chofer['municipio']}, {chofer['provincia']}\n"
            f"Mensaje: {update.message.text or '(sin texto)'}\n"
            f"🔗 ID: {user.id}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    await update.message.reply_text(
        "✅ *Comprobante enviado al administrador.*\n"
        "Te avisaremos cuando se confirme el pago (menos de 24h).",
        parse_mode="Markdown"
    )
