from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_choferes_pendientes, aprobar_chofer, rechazar_chofer,
    get_conn, confirmar_pago_chofer
)
from config import ADMIN_ID
from datetime import datetime, timedelta


def solo_admin(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id != ADMIN_ID:
            await update.message.reply_text("No tienes permiso para usar este comando.")
            return
        return await func(update, context)
    return wrapper


@solo_admin
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = get_conn()
    activos = conn.execute("SELECT COUNT(*) FROM choferes WHERE estado='activo'").fetchone()[0]
    pendientes = conn.execute("SELECT COUNT(*) FROM choferes WHERE estado='pendiente' OR estado='pendiente_pago'").fetchone()[0]
    print(f"DEBUG pendientes: {pendientes}")
    viajes_hoy = conn.execute("SELECT COUNT(*) FROM viajes WHERE date(fecha_creacion)=date('now')").fetchone()[0]
    viajes_mes = conn.execute("SELECT COUNT(*) FROM viajes WHERE strftime('%Y-%m', fecha_creacion)=strftime('%Y-%m', 'now')").fetchone()[0]
    ingresos = conn.execute("SELECT COUNT(*)*250 FROM pagos WHERE confirmado_por IS NOT NULL AND strftime('%Y-%m', fecha_pago)=strftime('%Y-%m', 'now')").fetchone()[0]
    conn.close()

    keyboard = [
        [InlineKeyboardButton(f"Pendientes ({pendientes})", callback_data="admin_ver_pendientes")],
        [InlineKeyboardButton("Estadisticas", callback_data="admin_stats")],
        [InlineKeyboardButton("Aviso a todos", callback_data="admin_broadcast")],
    ]

    await update.message.reply_text(
        f"Panel de Administracion\n\n"
        f"Choferes activos: {activos}\n"
        f"Choferes pendientes: {pendientes}\n"
        f"Viajes hoy: {viajes_hoy}\n"
        f"Viajes este mes: {viajes_mes}\n"
        f"Ingresos este mes: {ingresos} CUP",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "admin_ver_pendientes":
        pendientes = get_choferes_pendientes()
        if not pendientes:
            await query.edit_message_text("No hay choferes pendientes.")
            return
        for c in pendientes:
            keyboard = [[
                InlineKeyboardButton("Aprobar", callback_data=f"aprobar_{c['telegram_id']}"),
                InlineKeyboardButton("Rechazar", callback_data=f"rechazar_{c['telegram_id']}")
            ]]
            await context.bot.send_message(
                query.from_user.id,
                f"Solicitud de registro\n\n"
                f"Nombre: {c['nombre']}\n"
                f"Tel: {c['telefono']}\n"
                f"Provincia: {c['provincia']}\n"
                f"Municipio: {c['municipio']}\n"
                f"Vehiculo: {c['vehiculo']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )

    elif data.startswith("aprobar_"):
        chofer_id = int(data.split("_")[1])
        aprobar_chofer(chofer_id)
        try:
            await query.edit_message_text("Chofer aprobado. Esperando confirmacion de pago.")
        except:
            await query.answer("Chofer aprobado.")
        try:
            await context.bot.send_message(
                chofer_id,
                "Tu solicitud fue aprobada.\n\n"
                "Para activar tu cuenta y comenzar a recibir viajes "
                "debes pagar la cuota mensual de 250 CUP.\n\n"
                "Escribe /pagar para ver las instrucciones."
            )
        except Exception as e:
            print(f"Error notificando al chofer: {e}")

    elif data.startswith("rechazar_"):
        chofer_id = int(data.split("_")[1])
        rechazar_chofer(chofer_id)
        await query.edit_message_text("Chofer rechazado.")
        try:
            await context.bot.send_message(
                chofer_id,
                "Tu solicitud de registro fue rechazada.\n"
                "Puedes contactar al administrador para mas informacion."
            )
        except Exception as e:
            print(f"Error notificando al chofer: {e}")

    elif data.startswith("admin_pago_"):
        chofer_id = int(data.split("_")[2])
        fecha_vence = (datetime.now() + timedelta(days=30)).strftime("%d/%m/%Y")
        confirmar_pago_chofer(chofer_id)
        try:
            await query.edit_message_caption(caption=f"Pago confirmado. Chofer activo hasta {fecha_vence}.")
        except:
            await query.edit_message_text(f"Pago confirmado. Chofer activo hasta {fecha_vence}.")
        print(f"Intentando notificar al chofer {chofer_id}")
        try:
            await context.bot.send_message(
                chofer_id,
                f"Tu pago fue confirmado.\n\n"
                f"Tu cuenta esta activa hasta el {fecha_vence}.\n"
                f"Ya puedes recibir viajes directamente aqui.\n\n"
                f"3 dias antes del vencimiento te avisaremos para renovar."
            )
        except Exception as e:
            print(f"Error notificando al chofer: {e}")
