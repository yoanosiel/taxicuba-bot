from telegram import Update
from telegram.ext import ContextTypes
from database import (
    get_embajador, registrar_embajador, get_referidos_de_embajador
)
import random
import string

def generar_codigo(nombre):
    iniciales = nombre.strip().upper().replace(" ", "")[:6]
    sufijo = ''.join(random.choices(string.digits, k=3))
    return f"EMB{iniciales}{sufijo}"

async def embajador_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    embajador = get_embajador(user.id)

    if embajador:
        referidos = get_referidos_de_embajador(user.id)
        activos = [r for r in referidos if r['estado'] == 'activo']
        await update.message.reply_text(
            f"Tu perfil de Embajador TaxiCuba\n\n"
            f"Codigo de referido: {embajador['codigo']}\n\n"
            f"Comparte este codigo con los choferes.\n"
            f"Ellos deben escribir /start {embajador['codigo']} al registrarse.\n\n"
            f"Choferes referidos: {len(referidos)}\n"
            f"Choferes activos: {len(activos)}\n\n"
            f"Saldo acumulado: {embajador['saldo']} CUP\n"
            f"Total ganado: {embajador['total_ganado']} CUP\n\n"
            f"Para cobrar tu saldo contacta al admin."
        )
        return

    codigo = generar_codigo(user.full_name)
    registrar_embajador(user.id, user.full_name, codigo)

    await update.message.reply_text(
        f"Bienvenido al programa de Embajadores TaxiCuba!\n\n"
        f"Tu codigo de referido es:\n"
        f"{codigo}\n\n"
        f"Comparte este codigo con los choferes.\n"
        f"Ellos deben escribir /start {codigo} al registrarse.\n\n"
        f"Ganaras:\n"
        f"250 CUP por cada chofer nuevo que pague\n"
        f"50 CUP cada vez que ese chofer renueve\n\n"
        f"El chofer referido obtiene 60 dias activo por el precio de 1 mes.\n\n"
        f"Escribe /embajador en cualquier momento para ver tus estadisticas."
    )
