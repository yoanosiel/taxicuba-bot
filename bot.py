"""
TaxiCuba Bot - Sistema de transporte privado via Telegram
"""

import logging
from dotenv import load_dotenv
load_dotenv()
import os
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters
)
from database import init_db
from handlers.start import start_handler
from handlers.chofer import chofer_conv_handler
from handlers.cliente import cliente_conv_handler
from handlers.admin import admin_panel as admin_handler, admin_callback
from handlers.pagar import pagar_handler, recibir_comprobante
from handlers.perfil import perfil_handler
from handlers.viaje import chofer_acepta_viaje, procesar_valoracion, guardar_estrella
from handlers.embajador import embajador_handler
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

    # Comandos principales
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(chofer_conv_handler())
    app.add_handler(cliente_conv_handler())
    app.add_handler(CommandHandler("admin", admin_handler))
    app.add_handler(CommandHandler("pagar", pagar_handler))
    app.add_handler(CommandHandler("perfil", perfil_handler))
    app.add_handler(CommandHandler("ayuda", start_handler))
    app.add_handler(CommandHandler("embajador", embajador_handler))

    # Callbacks de botones inline
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^admin_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^aprobar_"))
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^rechazar_"))
    
    app.add_handler(CallbackQueryHandler(chofer_acepta_viaje, pattern="^aceptar_viaje_"))
    app.add_handler(CallbackQueryHandler(procesar_valoracion, pattern="^valorar_"))
    app.add_handler(CallbackQueryHandler(guardar_estrella, pattern="^stars_"))

    # Recibir fotos de comprobantes de pago
    app.add_handler(MessageHandler(filters.PHOTO, recibir_comprobante))

    # Tareas programadas
    setup_jobs(app)

    logger.info("Bot TaxiCuba iniciado...")
    app.run_polling()


if __name__ == "__main__":
    main()
