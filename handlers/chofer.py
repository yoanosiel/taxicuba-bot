"""
Registro de choferes — conversación paso a paso
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, filters, CommandHandler
)
from database import registrar_chofer, get_chofer
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
        "🚗 *Registro de Chofer*\n\n"
        "Vamos paso a paso. Puedes cancelar en cualquier momento escribiendo /cancelar\n\n"
        "Paso 1/5: ¿Cuál es tu *nombre completo*?",
        parse_mode="Markdown"
    )
    return NOMBRE


async def recibir_nombre(update: Update, context: ContextTypes.DEFAULT_TYPE):
    nombre = update.message.text.strip()
    if len(nombre) < 4:
        await update.message.reply_text("❌ Nombre muy corto. Escribe tu nombre completo:")
        return NOMBRE
    context.user_data['nombre'] = nombre

    await update.message.reply_text(
        f"✅ Nombre: *{nombre}*\n\n"
        f"Paso 2/5: ¿Cuál es tu número de *teléfono*? (8 dígitos, ej: 55123456)",
        parse_mode="Markdown"
    )
    return TELEFONO


async def recibir_telefono(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tel = update.message.text.strip().replace(" ", "").replace("-", "")
    if not (tel.isdigit() and len(tel) == 8 and tel.startswith("5")):
        await update.message.reply_text(
            "❌ Teléfono inválido. Debe ser un número cubano de 8 dígitos (ej: 55123456):"
        )
        return TELEFONO
    context.user_data['telefono'] = tel

    # Mostrar provincias como teclado
    keyboard = [[p] for p in LISTA_PROVINCIAS]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "Paso 3/5: ¿En qué *provincia* operas?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return PROVINCIA


async def recibir_provincia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    provincia = update.message.text.strip()
    municipios = get_municipios(provincia)
    if not municipios:
        await update.message.reply_text("❌ Provincia no válida. Selecciona una de la lista:")
        return PROVINCIA

    context.user_data['provincia'] = provincia

    keyboard = [[m] for m in municipios]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"Paso 4/5: ¿En qué *municipio* de {provincia} operas?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return MUNICIPIO


async def recibir_municipio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    municipio = update.message.text.strip()
    provincia = context.user_data.get('provincia', '')
    if municipio not in get_municipios(provincia):
        await update.message.reply_text("❌ Municipio no válido. Selecciona uno de la lista:")
        return MUNICIPIO

    context.user_data['municipio'] = municipio

    await update.message.reply_text(
        "Paso 5/5: Describe tu *vehículo* (marca, modelo, color)\n"
        "Ejemplo: _Lada 2107, azul_ o _Geely CK, blanco_",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return VEHICULO


async def recibir_vehiculo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    vehiculo = update.message.text.strip()
    if len(vehiculo) < 5:
        await update.message.reply_text("❌ Descripción muy corta. Ej: Lada 2107, azul")
        return VEHICULO

    context.user_data['vehiculo'] = vehiculo
    d = context.user_data

    keyboard = [
        [InlineKeyboardButton("✅ Confirmar Registro", callback_data="confirmar_registro_chofer")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_registro")],
    ]

    await update.message.reply_text(
        "📋 *Resumen de tu registro:*\n\n"
        f"👤 Nombre: {d['nombre']}\n"
        f"📞 Teléfono: {d['telefono']}\n"
        f"📍 Provincia: {d['provincia']}\n"
        f"🏘️ Municipio: {d['municipio']}\n"
        f"🚗 Vehículo: {d['vehiculo']}\n\n"
        f"💰 Cuota mensual: *250 CUP*\n\n"
        "¿Todo correcto?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return CONFIRMAR


async def confirmar_registro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    d = context.user_data

    registrar_chofer(
        user.id, user.username,
        d['nombre'], d['telefono'],
        d['provincia'], d['municipio'], d['vehiculo']
    )

    await query.edit_message_text(
        "✅ *¡Registro enviado!*\n\n"
        "Tu solicitud está *pendiente de aprobación*.\n"
        "El admin revisará tu registro y te avisará pronto.\n\n"
        "Una vez aprobado recibirás los viajes "
        "disponibles directamente aquí en este chat.",
            
        parse_mode="Markdown"
    )

    # Notificar al admin
    if ADMIN_ID:
        keyboard = [
            [
                InlineKeyboardButton("✅ Aprobar", callback_data=f"admin_aprobar_{user.id}"),
                InlineKeyboardButton("❌ Rechazar", callback_data=f"admin_rechazar_{user.id}"),
            ]
        ]
        await context.bot.send_message(
            ADMIN_ID,
            f"🆕 *Nuevo chofer pendiente:*\n\n"
            f"👤 {d['nombre']}\n"
            f"📞 {d['telefono']}\n"
            f"📍 {d['provincia']} — {d['municipio']}\n"
            f"🚗 {d['vehiculo']}\n"
            f"🔗 Telegram: @{user.username or 'sin_usuario'} (ID: {user.id})",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Registro cancelado. Escribe /start para volver a empezar.",
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
