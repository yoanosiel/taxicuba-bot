"""
Manejo de viajes: aceptación por el chofer y valoraciones
"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from database import (
    get_viaje, get_chofer, actualizar_viaje,
    update_rating_chofer, get_choferes_activos_por_provincia
)


async def chofer_acepta_viaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    chofer_id = query.from_user.id
    chofer = get_chofer(chofer_id)

    if not chofer:
        await query.answer("❌ No estás registrado como chofer.", show_alert=True)
        return

    if chofer['estado'] != 'activo':
        await query.answer("❌ Tu cuenta no está activa. Escribe /pagar si tu cuota venció.", show_alert=True)
        return

    viaje_id = int(query.data.split("_")[-1])
    viaje = get_viaje(viaje_id)

    if not viaje:
        await query.answer("❌ Este viaje ya no existe.", show_alert=True)
        return

    if viaje['estado'] != 'publicado':
        await query.answer("⚠️ Este viaje ya fue tomado por otro chofer.", show_alert=True)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    if chofer['provincia'] != viaje['provincia']:
        await query.answer("❌ Este viaje no es de tu provincia.", show_alert=True)
        return

    # Marcar el viaje como aceptado
    actualizar_viaje(viaje_id, estado='aceptado', chofer_id=chofer_id)

    # Notificar al CLIENTE con los datos del chofer
    equipaje_txt = "Sí" if viaje['equipaje'] else "No"
    try:
        keyboard = [[InlineKeyboardButton(
            "✅ Viaje completado — Valorar",
            callback_data=f"valorar_{viaje_id}_cliente"
        )]]
        await context.bot.send_message(
            viaje['cliente_id'],
            f"🎉 *¡Encontraste un chofer!*\n\n"
            f"👤 *Nombre:* {chofer['nombre']}\n"
            f"📞 *Teléfono:* {chofer['telefono']}\n"
            f"🚗 *Vehículo:* {chofer['vehiculo']}\n"
            f"⭐ *Valoración:* {chofer['rating']}/5.0\n\n"
            f"Ya puedes coordinar los detalles directamente con el chofer.\n"
            f"Cuando termines el viaje presiona el botón de abajo:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            
        )
    except Exception as e:
        print(f"Error notificando al cliente: {e}")

    # Confirmar al CHOFER que aceptó
    await query.edit_message_text(
        f"✅ *¡Viaje #{viaje_id} aceptado!*\n\n"
        f"📍 *Recogida:* {viaje['direccion_origen']}\n"
        f"🏁 *Destino:* {viaje['destino']}\n"
        f"👥 *Pasajeros:* {viaje['pasajeros']}   🧳 Equipaje: {equipaje_txt}\n"
        f"💰 *Precio acordado:* {viaje['precio_oferta']} CUP\n\n"
        f"El cliente ya tiene tu información. ¡Buen viaje! 🚗",
        
    )

    # Avisar a los DEMÁS choferes de la provincia que el viaje fue tomado
    otros_choferes = get_choferes_activos_por_provincia(viaje['provincia'])
    for otro in otros_choferes:
        if otro['telegram_id'] == chofer_id:
            continue
        try:
            await context.bot.send_message(
                otro['telegram_id'],
                f"ℹ️ El viaje *#{viaje_id}* "
                f"({viaje['municipio_origen']} → {viaje['destino']}) "
                f"ya fue tomado por otro chofer.",
                
            )
        except Exception:
            pass


async def procesar_valoracion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partes = query.data.split("_")
    viaje_id = int(partes[1])
    quien = partes[2]

    viaje = get_viaje(viaje_id)
    if not viaje:
        await query.edit_message_text("❌ Viaje no encontrado.")
        return

    if quien == 'cliente':
        actualizar_viaje(viaje_id, estado='completado')
        keyboard = [
            [
                InlineKeyboardButton("⭐ 1", callback_data=f"stars_{viaje_id}_1"),
                InlineKeyboardButton("⭐⭐ 2", callback_data=f"stars_{viaje_id}_2"),
                InlineKeyboardButton("⭐⭐⭐ 3", callback_data=f"stars_{viaje_id}_3"),
            ],
            [
                InlineKeyboardButton("⭐⭐⭐⭐ 4", callback_data=f"stars_{viaje_id}_4"),
                InlineKeyboardButton("⭐⭐⭐⭐⭐ 5", callback_data=f"stars_{viaje_id}_5"),
            ]
        ]
        await query.edit_message_text(
            "✅ *¡Viaje marcado como completado!*\n\n"
            "¿Cómo valorarías al chofer?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            
        )


async def guardar_estrella(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    partes = query.data.split("_")
    viaje_id = int(partes[1])
    estrellas = int(partes[2])

    viaje = get_viaje(viaje_id)
    if viaje and viaje['chofer_id']:
        actualizar_viaje(viaje_id, valoracion_cliente=estrellas)
        update_rating_chofer(viaje['chofer_id'], estrellas)
        await query.edit_message_text(
            f"{'⭐' * estrellas} *¡Gracias por tu valoración!*\n\n"
            f"Ayudas a mejorar el servicio para todos.",
            
        )
