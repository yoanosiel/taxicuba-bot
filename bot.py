"""
TaxiCuba Bot - Sistema de transporte privado via Telegram
Autor: Generado automáticamente
"""

import logging
from dotenv import load_dotenv
load_dotenv()
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters, ContextTypes
)
from database import init_db
from handlers.start import start_handler
from handlers.chofer import chofer_conv_handler
from handlers.cliente import cliente_conv_handler
from handlers.admin import admin_handler
from handlers.pagar import pagar_handler
from handlers.perfil import perfil_handler
from jobs import setup_jobs

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    TOKEN = os.environ.get("BOT_TOKEN")
    if not TOKEN:
        raise ValueError("Falta la variable de entorno BOT_TOKEN")

    init_db()

    app = Application.builder().token(TOKEN).build()

    # Handlers principales
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(chofer_conv_handler())
    app.add_handler(cliente_conv_handler())
    app.add_handler(CommandHandler("admin", admin_handler))
    app.add_handler(CommandHandler("pagar", pagar_handler))
    app.add_handler(CommandHandler("perfil", perfil_handler))
    app.add_handler(CommandHandler("ayuda", ayuda_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))

    # Tareas automáticas (avisos de cuota, expiración de viajes)
    setup_jobs(app)

    logger.info("Bot TaxiCuba iniciado...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


async def ayuda_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "🚖 *TaxiCuba Bot — Ayuda*\n\n"
        "Para *clientes*:\n"
        "• /start → Publicar un viaje\n"
        "• /perfil → Ver tus datos\n\n"
        "Para *choferes*:\n"
        "• /start → Registrarte\n"
        "• /pagar → Información de pago\n"
        "• /perfil → Ver tu estado y valoración\n\n"
        "Para *administrador*:\n"
        "• /admin → Panel de control\n\n"
        "❓ ¿Problemas? Escribe al administrador directamente."
    )
    await update.message.reply_text(texto, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja todos los botones inline que no están en conversaciones activas"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("aceptar_viaje_"):
        from handlers.viaje import chofer_acepta_viaje
        await chofer_acepta_viaje(update, context)
    elif data.startswith("admin_aprobar_"):
        from handlers.admin import aprobar_chofer
        await aprobar_chofer(update, context)
    elif data.startswith("admin_rechazar_"):
        from handlers.admin import rechazar_chofer
        await rechazar_chofer(update, context)
    elif data.startswith("admin_pago_"):
        from handlers.admin import confirmar_pago
        await confirmar_pago(update, context)
    elif data.startswith("valorar_"):
        from handlers.viaje import procesar_valoracion
        await procesar_valoracion(update, context)


if __name__ == "__main__":
    main()
