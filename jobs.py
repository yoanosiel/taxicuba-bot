"""
Tareas automáticas del bot:
- Expirar viajes sin chofer después de 30 minutos
- Avisar a choferes con cuota próxima a vencer
- Suspender choferes con cuota vencida
"""

import logging
from telegram.ext import Application
from database import get_viajes_expirados, actualizar_viaje, get_choferes_cuota_vencida, suspender_chofer

logger = logging.getLogger(__name__)


async def expirar_viajes(context):
    """Expira viajes que llevan más de 30 minutos sin chofer"""
    try:
        viajes = get_viajes_expirados()
        for viaje in viajes:
            actualizar_viaje(viaje['id'], estado='expirado')

            # Editar mensaje en el canal
            if viaje.get('canal_id') and viaje.get('mensaje_id'):
                try:
                    await context.bot.edit_message_text(
                        chat_id=viaje['canal_id'],
                        message_id=viaje['mensaje_id'],
                        text=(
                            f"⏰ *VIAJE #{viaje['id']} — EXPIRADO*\n\n"
                            f"📍 {viaje['direccion_origen']} → {viaje['destino']}\n"
                            f"_Nadie aceptó este viaje en 30 minutos_"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.warning(f"No se pudo editar mensaje expirado: {e}")

            # Notificar al cliente
            try:
                await context.bot.send_message(
                    viaje['cliente_id'],
                    f"⏰ *Tu viaje #{viaje['id']} expiró*\n\n"
                    f"Ningún chofer aceptó en 30 minutos.\n"
                    f"Puedes intentar de nuevo con /viaje, "
                    f"quizás con un precio un poco mayor.",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

            logger.info(f"Viaje #{viaje['id']} expirado.")
    except Exception as e:
        logger.error(f"Error en job expirar_viajes: {e}")


async def revisar_cuotas(context):
    """Suspende choferes con cuota vencida y les avisa"""
    try:
        choferes_vencidos = get_choferes_cuota_vencida()
        for chofer in choferes_vencidos:
            suspender_chofer(chofer['telegram_id'])
            try:
                await context.bot.send_message(
                    chofer['telegram_id'],
                    f"⛔ *Tu cuenta ha sido suspendida*\n\n"
                    f"Tu cuota mensual de 250 CUP ha vencido.\n"
                    f"Escribe /pagar para renovar y volver a recibir viajes.",
                    parse_mode="Markdown"
                )
            except Exception:
                pass
            logger.info(f"Chofer {chofer['nombre']} suspendido por cuota vencida.")
    except Exception as e:
        logger.error(f"Error en job revisar_cuotas: {e}")


def setup_jobs(app: Application):
    """Registra las tareas automáticas"""
    jq = app.job_queue

    # Revisar viajes expirados cada 5 minutos
    jq.run_repeating(expirar_viajes, interval=300, first=60)

    # Revisar cuotas vencidas una vez al día (a las 8 AM)
    jq.run_daily(revisar_cuotas, time=__import__('datetime').time(8, 0))

    logger.info("Tareas automáticas configuradas.")
