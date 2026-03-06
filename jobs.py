from datetime import datetime, timedelta
from database import get_conn


async def expirar_viajes(context):
    """Expira viajes sin chofer despues de 30 minutos"""
    conn = get_conn()
    viajes = conn.execute("""
        SELECT * FROM viajes WHERE estado='publicado'
        AND datetime(fecha_creacion, '+30 minutes') < datetime('now')
    """).fetchall()
    conn.close()

    for v in viajes:
        v = dict(v)
        conn = get_conn()
        conn.execute("UPDATE viajes SET estado='expirado' WHERE id=?", (v['id'],))
        conn.commit()
        conn.close()
        try:
            await context.bot.send_message(
                v['cliente_id'],
                f"Tu viaje #{v['id']} expiro sin que ningun chofer lo aceptara.\n"
                f"Puedes publicar uno nuevo con /viaje."
            )
        except Exception as e:
            print(f"Error notificando expiracion: {e}")


async def revisar_pagos(context):
    """Suspende choferes con pago vencido y avisa 3 dias antes"""
    conn = get_conn()
    choferes = conn.execute("""
        SELECT * FROM choferes WHERE estado='activo'
    """).fetchall()
    conn.close()

    hoy = datetime.now()

    for c in choferes:
        c = dict(c)
        if not c.get('fecha_pago'):
            continue

        fecha_pago = datetime.fromisoformat(c['fecha_pago'])
        dias_activo = (hoy - fecha_pago).days
        dias_restantes = 30 - dias_activo

        # Suspender si vencio
        if dias_restantes <= 0:
            conn = get_conn()
            conn.execute("""
                UPDATE choferes SET estado='pendiente_pago'
                WHERE telegram_id=?
            """, (c['telegram_id'],))
            conn.commit()
            conn.close()
            try:
                await context.bot.send_message(
                    c['telegram_id'],
                    "Tu cuota mensual ha vencido.\n\n"
                    "Tu cuenta esta suspendida temporalmente y no recibiras "
                    "nuevos viajes hasta que renueves.\n\n"
                    "Escribe /pagar para renovar tu cuota de 250 CUP y "
                    "volver a recibir viajes."
                )
            except Exception as e:
                print(f"Error suspendiendo chofer: {e}")

        # Avisar 3 dias antes
        elif dias_restantes == 3:
            try:
                await context.bot.send_message(
                    c['telegram_id'],
                    f"Tu cuota vence en 3 dias.\n\n"
                    f"Para no perder el acceso a los viajes renueva "
                    f"antes del vencimiento.\n\n"
                    f"Escribe /pagar para renovar tu cuota de 250 CUP."
                )
            except Exception as e:
                print(f"Error avisando vencimiento: {e}")

        # Avisar 1 dia antes
        elif dias_restantes == 1:
            try:
                await context.bot.send_message(
                    c['telegram_id'],
                    "Tu cuota vence MAÑANA.\n\n"
                    "Escribe /pagar ahora para no quedarte sin servicio."
                )
            except Exception as e:
                print(f"Error avisando vencimiento: {e}")


def setup_jobs(app):
    """Configura las tareas programadas"""
    job_queue = app.job_queue
    job_queue.run_repeating(expirar_viajes, interval=300, first=10)
    job_queue.run_repeating(revisar_pagos, interval=86400, first=60)
