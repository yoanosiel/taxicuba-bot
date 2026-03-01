"""
Panel de administración
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_choferes_pendientes, activar_chofer, suspender_chofer,
    registrar_pago_chofer, get_chofer, get_estadisticas
)
from config import ADMIN_ID


def solo_admin(func):
    """Decorador: solo el admin puede usar esta función"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            if update.message:
                await update.message.reply_text("❌ No tienes permiso para usar este comando.")
            return
        return await func(update, context)
    return wrapper


@solo_admin
async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = get_estadisticas()
    pendientes = get_choferes_pendientes()

    keyboard = [
        [InlineKeyboardButton(f"👥 Pendientes ({stats['choferes_pendientes']})", callback_data="admin_ver_pendientes")],
        [InlineKeyboardButton("📊 Estadísticas", callback_data="admin_estadisticas")],
        [InlineKeyboardButton("📢 Aviso a todos", callback_data="admin_broadcast")],
    ]

    await update.message.reply_text(
        f"🛠️ *Panel de Administración*\n\n"
        f"✅ Choferes activos: {stats['choferes_activos']}\n"
        f"⏳ Choferes pendientes: {stats['choferes_pendientes']}\n"
        f"🚖 Viajes hoy: {stats['viajes_hoy']}\n"
        f"📅 Viajes este mes: {stats['viajes_mes']}\n"
        f"💰 Ingresos estimados: {stats['ingresos_mes']} CUP",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def aprobar_chofer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Sin permiso.", show_alert=True)
        return

    chofer_id = int(query.data.split("_")[-1])
    chofer = get_chofer(chofer_id)

    if not chofer:
        await query.answer("❌ Chofer no encontrado.", show_alert=True)
        return

    activar_chofer(chofer_id)
    await query.answer("✅ Chofer aprobado.")
    await query.edit_message_text(
        query.message.text + f"\n\n✅ *APROBADO por admin*",
        parse_mode="Markdown"
    )

    # Notificar al chofer
    try:
        from config import CANALES_PROVINCIAS
        canal = CANALES_PROVINCIAS.get(chofer['provincia'], 'el canal de tu provincia')
        await context.bot.send_message(
            chofer_id,
            f"🎉 *¡Tu cuenta ha sido aprobada!*\n\n"
            f"Ya puedes ver los viajes disponibles en tu zona.\n\n"
            f"📌 *Siguiente paso:* Únete al canal de *{chofer['provincia']}* "
            f"para recibir las solicitudes de viaje.\n\n"
            f"Recuerda que tu cuota mensual es de *250 CUP*. "
            f"Escribe /pagar cuando necesites renovar.",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Error notificando al chofer aprobado: {e}")


async def rechazar_chofer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Sin permiso.", show_alert=True)
        return

    chofer_id = int(query.data.split("_")[-1])
    suspender_chofer(chofer_id)
    await query.answer("Chofer rechazado.")
    await query.edit_message_text(
        query.message.text + f"\n\n❌ *RECHAZADO por admin*",
        parse_mode="Markdown"
    )

    try:
        await context.bot.send_message(
            chofer_id,
            "❌ *Tu solicitud de registro fue rechazada.*\n\n"
            "Si crees que es un error, comunícate con el administrador.",
            parse_mode="Markdown"
        )
    except Exception:
        pass


async def confirmar_pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.from_user.id != ADMIN_ID:
        await query.answer("❌ Sin permiso.", show_alert=True)
        return

    chofer_id = int(query.data.split("_")[-1])
    registrar_pago_chofer(chofer_id, query.from_user.id)
    await query.answer("✅ Pago confirmado.")

    chofer = get_chofer(chofer_id)
    await query.edit_message_text(
        query.message.text + f"\n\n✅ *PAGO CONFIRMADO* — Cuenta activada",
        parse_mode="Markdown"
    )

    try:
        await context.bot.send_message(
            chofer_id,
            "✅ *¡Pago confirmado!*\n\n"
            "Tu cuenta está activa por los próximos 30 días.\n"
            "¡A trabajar! 🚗",
            parse_mode="Markdown"
        )
    except Exception:
        pass
