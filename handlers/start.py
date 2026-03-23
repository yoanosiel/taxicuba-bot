"""
Handler de inicio — detecta si el usuario es chofer o cliente
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import get_chofer, get_cliente, registrar_cliente, get_embajador_por_codigo


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    telegram_id = user.id

    # Detectar codigo de referido
    if context.args:
        codigo = context.args[0]
        embajador = get_embajador_por_codigo(codigo)
        if embajador:
            context.user_data['referido_por'] = codigo
            await update.message.reply_text(
                "Vienes referido por un embajador TaxiCuba.\n"
                "Al registrarte como chofer y pagar obtendras 60 dias activo por el precio de 1 mes."
            )

    # Ver si ya esta registrado como chofer
    chofer = get_chofer(telegram_id)
    if chofer:
        estado = chofer['estado']
        if estado == 'activo':
            await update.message.reply_text(
                f"Bienvenido de nuevo, {chofer['nombre']}\n\n"
                f"Tu cuenta esta activa.\n"
                f"Vehiculo: {chofer['vehiculo']}\n"
                f"Zona: {chofer['municipio']}, {chofer['provincia']}\n"
                f"Valoracion: {chofer['rating']}/5.0\n\n"
                f"Los viajes te llegaran directamente aqui en este chat."
            )
        elif estado == 'pendiente':
            await update.message.reply_text(
                "Tu registro esta pendiente de aprobacion.\n\n"
                "El administrador revisara tu solicitud pronto. "
                "Te avisaremos cuando tu cuenta este activa."
            )
        elif estado == 'pendiente_pago':
            await update.message.reply_text(
                "Tu solicitud fue aprobada.\n\n"
                "Para activar tu cuenta escribe /pagar y sigue las instrucciones."
            )
        elif estado == 'suspendido':
            await update.message.reply_text(
                "Tu cuenta esta suspendida.\n\n"
                "Esto puede ser por cuota vencida. Escribe /pagar para renovar."
            )
        return

    # Ver si ya esta registrado como cliente
    cliente = get_cliente(telegram_id)
    if cliente:
        await update.message.reply_text(
            f"Bienvenido de nuevo!\n\n"
            f"Para pedir un taxi escribe /viaje\n"
            f"Para ver tu perfil escribe /perfil"
        )
        return

    # Usuario nuevo — preguntar rol
    keyboard = [
        [InlineKeyboardButton("Soy Chofer", callback_data="rol_chofer")],
        [InlineKeyboardButton("Soy Cliente", callback_data="rol_cliente")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Bienvenido a TaxiCuba Bot\n\n"
        "El sistema de transporte privado mas facil de Cuba.\n\n"
        "Como quieres registrarte?",
        reply_markup=reply_markup
    )
