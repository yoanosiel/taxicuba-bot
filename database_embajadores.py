def registrar_embajador(telegram_id, nombre, codigo):
    conn = get_conn()
    conn.execute("""
        INSERT OR IGNORE INTO embajadores (telegram_id, nombre, codigo, fecha_registro)
        VALUES (?, ?, ?, ?)
    """, (telegram_id, nombre, codigo, datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_embajador(telegram_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM embajadores WHERE telegram_id=?", (telegram_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_embajador_por_codigo(codigo):
    conn = get_conn()
    row = conn.execute("SELECT * FROM embajadores WHERE codigo=?", (codigo,)).fetchone()
    conn.close()
    return dict(row) if row else None

def get_referidos_de_embajador(telegram_id):
    conn = get_conn()
    rows = conn.execute("SELECT * FROM choferes WHERE referido_por=?", (str(telegram_id),)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def acreditar_comision(embajador_id, monto):
    conn = get_conn()
    conn.execute("""
        UPDATE embajadores SET saldo=saldo+?, total_ganado=total_ganado+?
        WHERE telegram_id=?
    """, (monto, monto, embajador_id))
    conn.commit()
    conn.close()

def es_primer_pago_chofer(chofer_id):
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM pagos WHERE chofer_id=?", (chofer_id,)).fetchone()[0]
    conn.close()
    return count == 0
