"""
Registro de choferes — conversación paso a paso
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, filters, CommandHandler
)
from database import registrar_chofer, get_chofer, get_embajador_por_codigo
from provincias import LISTA_PROVINCIAS, get_municipios
from config import ADMIN_ID

# Estados de la conversación
(NOMBRE, TELEFONO, PROVINCIA, MUNICIPIO, VEHICULO, CONFIRMAR) = range(6)


async def inicio_chofer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if get_chofer(query.from_user.id):
        await query.edit_message_text("Ya tienes un registro como chofer. Escribe /start")
        return ConversationHandler.END

    await query.edit_message_text(
        "Registro de Chofer\n\n"
        "Vamos paso a paso. Puedes cancelar en cualquier momento escribiendo /cancelar\n\n"
        "Paso 1/5: Cual es tu nombre completo?"
    )
    return NOMBRE


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    if len(nombre) < 4:
        await update.message.reply_text("Nombre muy corto. Escribe tu nombre completo:")
        return NOMBRE
    context.user_data['nombre'] = nombre

    await update.message.reply_text(
        f"Nombre: {nombre}\n\n"
        f"Paso 2/5: Cual es tu numero de telefono? (8 digitos, ej: 55123456)"
    )
    return TELEFONO


async def recibir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tel = update.message.text.strip().replace(" ", "").replace("-", "")
    if not (tel.isdigit() and len(tel) == 8 and tel.startswith("5")):
        await update.message.reply_text(
            "Telefono invalido. Debe ser un numero cubano de 8 digitos (ej: 55123456):"
        )
        return TELEFONO
    context.user_data['telefono'] = tel

    keyboard = [[p] for p in LISTA_PROVINCIAS]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Paso 3/5: En que provincia operas?",
        reply_markup=markup
    )
    return PROVINCIA


async def recibir_provincia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    provincia = update.message.text.strip()
    municipios = get_municipios(provincia)
    if not municipios:
        await update.message.reply_text("Provincia no valida. Selecciona una de la lista:")
        return PROVINCIA

    context.user_data['provincia'] = provincia

    keyboard = [[m] for m in municipios]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"Paso 4/5: En que municipio de {provincia} operas?",
        reply_markup=markup
    )
    return MUNICIPIO


async def recibir_municipio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    municipio = update.message.text.strip()
    provincia = context.user_data.get('provincia', '')
    if municipio not in get_municipios(provincia):
        await update.message.reply_text("Municipio no valido. Selecciona uno de la lista:")
        return MUNICIPIO

    context.user_data['municipio'] = municipio

    await update.message.reply_text(
        "Paso 5/5: Describe tu vehiculo (marca, modelo, color)\n"
        "Ejemplo: Lada 2107, azul o Geely CK, blanco",
        reply_markup=ReplyKeyboardRemove()
    )
    return VEHICULO


async def recibir_vehiculo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vehiculo = update.message.text.strip()
    if len(vehiculo) < 5:
        await update.message.reply_text("Descripcion muy corta. Ej: Lada 2107, azul")
        return VEHICULO

    context.user_data['vehiculo'] = vehiculo
    d = context.user_data

    keyboard = [
        [InlineKeyboardButton("Confirmar Registro", callback_data="confirmar_registro_chofer")],
        [InlineKeyboardButton("Cancelar", callback_data="cancelar_registro")],
    ]

    await update.message.reply_text(
        f"Resumen de tu registro:\n\n"
        f"Nombre: {d['nombre']}\n"
        f"Telefono: {d['telefono']}\n"
        f"Provincia: {d['provincia']}\n"
        f"Municipio: {d['municipio']}\n"
        f"Vehiculo: {d['vehiculo']}\n\n"
        f"Cuota mensual: 250 CUP\n\n"
        "Todo correcto?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CONFIRMAR


async def confirmar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    d = context.user_data

    # Verificar si viene referido por un embajador
    referido_por = context.user_data.get('referido_por', None)

    registrar_chofer(
        user.id, user.username,
        d['nombre'], d['telefono'],
        d['provincia'], d['municipio'], d['vehiculo'],
        referido_por=referido_por
    )

    msg_extra = ""
    if referido_por:
        msg_extra = "\n\nVienes referido por un embajador. Al activar tu cuenta tendras 60 dias por el precio de 1 mes."

    await query.edit_message_text(
        "Registro enviado!\n\n"
        "Tu solicitud esta pendiente de aprobacion.\n"
        "El admin revisara tu registro y te avisara pronto.\n\n"
        "Una vez aprobado recibiras los viajes directamente aqui en este chat."
        + msg_extra
    )

    if ADMIN_ID:
        referido_txt = f"\nReferido por: {referido_por}" if referido_por else ""
        keyboard = [[
            InlineKeyboardButton("Aprobar", callback_data=f"aprobar_{user.id}"),
            InlineKeyboardButton("Rechazar", callback_data=f"rechazar_{user.id}")
        ]]
        await context.bot.send_message(
            ADMIN_ID,
            f"Nuevo chofer pendiente:\n\n"
            f"Nombre: {d['nombre']}\n"
            f"Tel: {d['telefono']}\n"
            f"Provincia: {d['provincia']} - {d['municipio']}\n"
            f"Vehiculo: {d['vehiculo']}\n"
            f"Telegram: @{user.username or 'sin_usuario'} (ID: {user.id})"
            + referido_txt,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "Registro cancelado. Escribe /start para volver a empezar.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def chofer_conv_handler():
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(inicio_chofer, pattern="^rol_chofer$")],
        states={
            NOMBRE:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_nombre)],
            TELEFONO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_telefono)],
            PROVINCIA: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_provincia)],
            MUNICIPIO: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_municipio)],
            VEHICULO:  [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_vehiculo)],
            CONFIRMAR: [CallbackQueryHandler(confirmar_registro, pattern="^confirmar_registro_chofer$")],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True
    )
