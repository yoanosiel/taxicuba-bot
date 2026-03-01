"""
Flujo del cliente para solicitar un viaje
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes, ConversationHandler, CallbackQueryHandler,
    MessageHandler, CommandHandler, filters
)
from database import (
    registrar_cliente, get_cliente, crear_viaje,
    actualizar_viaje, cliente_tiene_viaje_activo
)
from provincias import LISTA_PROVINCIAS, get_municipios
from config import PRECIO_MINIMO_CUP
from datetime import datetime

# Estados
(PROV_CLIENTE, MUNIC_ORIGEN, DIR_ORIGEN, DESTINO,
 PASAJEROS, EQUIPAJE, PRECIO, PUBLICAR) = range(8)


async def inicio_cliente(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user

    registrar_cliente(user.id, user.username)

    if cliente_tiene_viaje_activo(user.id):
        await query.edit_message_text(
            "⚠️ Ya tienes un viaje activo o en curso.\n"
            "Espera a que termine o sea aceptado antes de publicar otro."
        )
        return ConversationHandler.END

    keyboard = [[p] for p in LISTA_PROVINCIAS]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await query.edit_message_text("¡Vamos a pedir tu taxi! 🚖")
    await context.bot.send_message(
        user.id,
        "📍 *Paso 1/6:* ¿En qué *provincia* te encuentras?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return PROV_CLIENTE


async def viaje_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /viaje directo para clientes ya registrados"""
    user = update.effective_user
    registrar_cliente(user.id, user.username)

    if cliente_tiene_viaje_activo(user.id):
        await update.message.reply_text(
            "⚠️ Ya tienes un viaje activo.\n"
            "Espera a que tu viaje actual sea aceptado o expire."
        )
        return ConversationHandler.END

    keyboard = [[p] for p in LISTA_PROVINCIAS]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "📍 *Paso 1/6:* ¿En qué *provincia* te encuentras?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return PROV_CLIENTE


async def recibir_provincia(update: Update, context: ContextTypes.DEFAULT_TYPE):
    provincia = update.message.text.strip()
    municipios = get_municipios(provincia)
    if not municipios:
        await update.message.reply_text("❌ Provincia no válida. Selecciona de la lista:")
        return PROV_CLIENTE

    context.user_data['provincia'] = provincia

    keyboard = [[m] for m in municipios]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        f"📍 *Paso 2/6:* ¿En qué *municipio* te recogen?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return MUNIC_ORIGEN


async def recibir_municipio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    municipio = update.message.text.strip()
    if municipio not in get_municipios(context.user_data.get('provincia', '')):
        await update.message.reply_text("❌ Municipio no válido. Selecciona de la lista:")
        return MUNIC_ORIGEN

    context.user_data['municipio_origen'] = municipio

    await update.message.reply_text(
        "📍 *Paso 3/6:* Escribe la *dirección exacta* de recogida\n"
        "_(calle, número, entre qué calles)_\n"
        "Ejemplo: _Calle 23 #456 e/ L y M, Vedado_",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return DIR_ORIGEN


async def recibir_direccion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    direccion = update.message.text.strip()
    if len(direccion) < 8:
        await update.message.reply_text("❌ Dirección muy corta. Sé más específico:")
        return DIR_ORIGEN

    context.user_data['direccion_origen'] = direccion

    await update.message.reply_text(
        "🏁 *Paso 4/6:* ¿A dónde vas? Escribe el *destino*\n"
        "_(municipio o dirección de destino)_",
        parse_mode="Markdown"
    )
    return DESTINO


async def recibir_destino(update: Update, context: ContextTypes.DEFAULT_TYPE):
    destino = update.message.text.strip()
    if len(destino) < 4:
        await update.message.reply_text("❌ Destino muy corto. Escribe más detalle:")
        return DESTINO

    context.user_data['destino'] = destino

    keyboard = [["1", "2", "3", "4+"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "👥 *Paso 5/6:* ¿Cuántos pasajeros van?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return PASAJEROS


async def recibir_pasajeros(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        pasajeros = int(texto.replace("+", "")) if texto != "4+" else 4
        if pasajeros < 1 or pasajeros > 8:
            raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Número no válido. Escribe 1, 2, 3 o 4+")
        return PASAJEROS

    context.user_data['pasajeros'] = pasajeros

    keyboard = [["🧳 Sí, llevo equipaje", "🎒 No, sin equipaje"]]
    markup = ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(
        "🧳 *Paso 6/6:* ¿Llevas equipaje grande?",
        reply_markup=markup,
        parse_mode="Markdown"
    )
    return EQUIPAJE


async def recibir_equipaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text
    equipaje = 1 if "Sí" in texto else 0
    context.user_data['equipaje'] = equipaje

    await update.message.reply_text(
        f"💰 ¿Cuánto ofreces por el viaje? (mínimo {PRECIO_MINIMO_CUP} CUP)\n\n"
        "Escribe solo el número, sin letras.\n"
        "Ejemplo: _250_",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode="Markdown"
    )
    return PRECIO


async def recibir_precio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip()
    try:
        precio = int(texto)
        if precio < PRECIO_MINIMO_CUP:
            await update.message.reply_text(
                f"❌ El precio mínimo es {PRECIO_MINIMO_CUP} CUP. Intenta de nuevo:"
            )
            return PRECIO
    except ValueError:
        await update.message.reply_text("❌ Escribe solo el número. Ej: 200")
        return PRECIO

    context.user_data['precio'] = precio
    d = context.user_data

    equipaje_txt = "Sí 🧳" if d['equipaje'] else "No 🎒"

    keyboard = [
        [InlineKeyboardButton("✅ Publicar viaje", callback_data="publicar_viaje")],
        [InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_viaje")],
    ]

    await update.message.reply_text(
        "📋 *Resumen de tu viaje:*\n\n"
        f"📍 Recogida: {d['municipio_origen']}, {d['provincia']}\n"
        f"🏠 Dirección: {d['direccion_origen']}\n"
        f"🏁 Destino: {d['destino']}\n"
        f"👥 Pasajeros: {d['pasajeros']}\n"
        f"🧳 Equipaje: {equipaje_txt}\n"
        f"💰 Oferta: *{d['precio']} CUP*\n\n"
        "¿Publicamos el viaje?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return PUBLICAR


async def publicar_viaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    d = context.user_data

    viaje_id = crear_viaje(
        cliente_id=user.id,
        provincia=d['provincia'],
        municipio_origen=d['municipio_origen'],
        direccion_origen=d['direccion_origen'],
        destino=d['destino'],
        pasajeros=d['pasajeros'],
        equipaje=d['equipaje'],
        precio_oferta=d['precio']
    )

    equipaje_txt = "Sí 🧳" if d['equipaje'] else "No 🎒"
    hora = datetime.now().strftime("%I:%M %p")
    username_link = f"@{user.username}" if user.username else f"[Contactar](tg://user?id={user.id})"

    texto_notif = (
        f"🚖 *NUEVO VIAJE DISPONIBLE #{viaje_id}*\n\n"
        f"📍 *Recogida:* {d['direccion_origen']}\n"
        f"🏘️ *Municipio:* {d['municipio_origen']}, {d['provincia']}\n"
        f"🏁 *Destino:* {d['destino']}\n"
        f"👥 *Pasajeros:* {d['pasajeros']}   🧳 *Equipaje:* {equipaje_txt}\n"
        f"💰 *Oferta del cliente:* {d['precio']} CUP\n"
        f"📞 *Cliente:* {username_link}\n"
        f"⏰ *Publicado:* {hora} — Válido 30 minutos"
    )

    keyboard = [[InlineKeyboardButton("✅ Acepto este viaje", callback_data=f"aceptar_viaje_{viaje_id}")]]

    # Notificar a todos los choferes activos de la provincia directamente en privado
    from database import get_choferes_activos_por_provincia
    choferes = get_choferes_activos_por_provincia(d['provincia'])
    notificados = 0
    for chofer in choferes:
        try:
            await context.bot.send_message(
                chofer['telegram_id'],
                texto_notif,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode="Markdown"
            )
            notificados += 1
        except Exception as e:
            # El chofer bloqueó el bot o nunca le escribió — se ignora
            print(f"No se pudo notificar al chofer {chofer['nombre']} ({chofer['telegram_id']}): {e}")

    await query.edit_message_text(
        f"✅ *¡Viaje publicado!* (#{viaje_id})\n\n"
        f"📨 Se notificó a *{notificados} chofer{'es' if notificados != 1 else ''}* "
        f"disponible{'s' if notificados != 1 else ''} en *{d['provincia']}*.\n\n"
        f"Te avisaremos cuando alguien acepte.\n"
        f"⏰ Expira en 30 minutos si nadie acepta.",
        parse_mode="Markdown"
    )

    context.user_data.clear()
    return ConversationHandler.END



async def cancelar_viaje_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    await query.edit_message_text("❌ Solicitud cancelada.")
    return ConversationHandler.END


async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Cancelado. Escribe /viaje cuando quieras pedir un taxi.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def cliente_conv_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(inicio_cliente, pattern="^rol_cliente$"),
            CommandHandler("viaje", viaje_cmd),
        ],
        states={
            PROV_CLIENTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_provincia)],
            MUNIC_ORIGEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_municipio)],
            DIR_ORIGEN:   [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_direccion)],
            DESTINO:      [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_destino)],
            PASAJEROS:    [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_pasajeros)],
            EQUIPAJE:     [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_equipaje)],
            PRECIO:       [MessageHandler(filters.TEXT & ~filters.COMMAND, recibir_precio)],
            PUBLICAR:     [
                CallbackQueryHandler(publicar_viaje, pattern="^publicar_viaje$"),
                CallbackQueryHandler(cancelar_viaje_btn, pattern="^cancelar_viaje$"),
            ],
        },
        fallbacks=[CommandHandler("cancelar", cancelar)],
        allow_reentry=True
    )
