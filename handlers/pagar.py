from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_chofer
from config import ADMIN_ID, INFO_PAGO


async def pagar_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chofer = get_chofer(user_id)

    if not chofer:
        await update.message.reply_text(
            "Este comando es solo para choferes registrados.\n"
            "Escribe /start para registrarte."
        )
        return

    if chofer['estado'] == 'activo':
        from database import get_conn
        from datetime import datetime
        conn = get_conn()
        pago = conn.execute("""
            SELECT fecha_pago FROM choferes WHERE telegram_id=?
        """, (user_id,)).fetchone()
        conn.close()

        if pago and pago['fecha_pago']:
            fecha_vence = datetime.fromisoformat(pago['fecha_pago'])
            dias_restantes = (fecha_vence - datetime.now()).days
            await update.message.reply_text(
                f"Tu cuenta esta activa.\n\n"
                f"Tu cuota vence en {dias_restantes} dias.\n\n"
                f"Si deseas renovar anticipadamente:\n\n"
                f"{INFO_PAGO}\n\n"
                f"Envia la foto del comprobante aqui mismo."
            )
            context.user_data['esperando_comprobante'] = True
            return

    await update.message.reply_text(
        f"Para activar tu cuenta debes pagar la cuota mensual de 250 CUP.\n\n"
        f"{INFO_PAGO}"
    )
    await update.message.reply_text(
        "Envia la foto del comprobante de pago aqui mismo.\n"
        "El admin la recibira y confirmara tu pago en menos de 24 horas."
    )
    context.user_data['esperando_comprobante'] = True


async def recibir_comprobante(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('esperando_comprobante'):
        return

    user = update.effective_user
    chofer = get_chofer(user.id)
    if not chofer:
        return

    context.user_data['esperando_comprobante'] = False

    keyboard = [[InlineKeyboardButton(
        "Confirmar Pago",
        callback_data=f"admin_pago_{user.id}"
    )]]

    if update.message.photo:
        await context.bot.send_photo(
            ADMIN_ID,
            update.message.photo[-1].file_id,
            caption=(
                f"Comprobante de pago recibido\n\n"
                f"Chofer: {chofer['nombre']}\n"
                f"Tel: {chofer['telefono']}\n"
                f"Provincia: {chofer['provincia']}\n"
                f"Municipio: {chofer['municipio']}\n"
                f"@{user.username or 'sin usuario'} (ID: {user.id})"
            ),
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await context.bot.send_message(
            ADMIN_ID,
            f"Pago reportado sin imagen\n\n"
            f"Chofer: {chofer['nombre']}\n"
            f"Tel: {chofer['telefono']}\n"
            f"ID: {user.id}",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    await update.message.reply_text(
        "Comprobante enviado al administrador.\n"
        "Te avisaremos cuando se confirme tu pago.\n\n"
        "El proceso toma menos de 24 horas."
    )
