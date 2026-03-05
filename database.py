"""
Base de datos SQLite para TaxiCuba Bot
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "taxicuba.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Crea todas las tablas si no existen"""
    conn = get_conn()
    c = conn.cursor()

    c.executescript("""
        CREATE TABLE IF NOT EXISTS choferes (
            telegram_id     INTEGER PRIMARY KEY,
            username        TEXT,
            nombre          TEXT NOT NULL,
            telefono        TEXT NOT NULL,
            provincia       TEXT NOT NULL,
            municipio       TEXT NOT NULL,
            vehiculo        TEXT NOT NULL,
            estado          TEXT DEFAULT 'pendiente',
            fecha_registro  TEXT DEFAULT (datetime('now')),
            fecha_pago      TEXT,
            rating          REAL DEFAULT 0.0,
            viajes_total    INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS clientes (
            telegram_id     INTEGER PRIMARY KEY,
            username        TEXT,
            telefono        TEXT,
            provincia       TEXT,
            rating          REAL DEFAULT 0.0,
            viajes_total    INTEGER DEFAULT 0,
            fecha_registro  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS viajes (
            id                  INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id          INTEGER NOT NULL,
            chofer_id           INTEGER,
            provincia           TEXT NOT NULL,
            municipio_origen    TEXT NOT NULL,
            direccion_origen    TEXT NOT NULL,
            destino             TEXT NOT NULL,
            pasajeros           INTEGER NOT NULL,
            equipaje            INTEGER DEFAULT 0,
            precio_oferta       INTEGER NOT NULL,
            estado              TEXT DEFAULT 'publicado',
            fecha_creacion      TEXT DEFAULT (datetime('now')),
            mensaje_id          INTEGER,
            canal_id            TEXT,
            valoracion_cliente  INTEGER,
            valoracion_chofer   INTEGER,
            FOREIGN KEY(cliente_id) REFERENCES clientes(telegram_id),
            FOREIGN KEY(chofer_id) REFERENCES choferes(telegram_id)
        );

        CREATE TABLE IF NOT EXISTS pagos (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            chofer_id       INTEGER NOT NULL,
            monto           INTEGER DEFAULT 250,
            fecha_pago      TEXT DEFAULT (datetime('now')),
            mes_pagado      TEXT NOT NULL,
            confirmado_por  INTEGER,
            FOREIGN KEY(chofer_id) REFERENCES choferes(telegram_id)
        );
    """)

    conn.commit()
    conn.close()
    print("Base de datos inicializada correctamente.")


# ──────────────────────────────────────────────
# FUNCIONES DE CHOFERES
# ──────────────────────────────────────────────

def registrar_chofer(telegram_id, username, nombre, telefono, provincia, municipio, vehiculo):
    conn = get_conn()
    conn.execute("""
        INSERT OR REPLACE INTO choferes
        (telegram_id, username, nombre, telefono, provincia, municipio, vehiculo, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pendiente')
    """, (telegram_id, username, nombre, telefono, provincia, municipio, vehiculo))
    conn.commit()
    conn.close()


def get_chofer(telegram_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM choferes WHERE telegram_id=?", (telegram_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def activar_chofer(telegram_id):
    conn = get_conn()
    conn.execute("UPDATE choferes SET estado='activo' WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()


def suspender_chofer(telegram_id):
    conn = get_conn()
    conn.execute("UPDATE choferes SET estado='suspendido' WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()


def registrar_pago_chofer(telegram_id, confirmado_por):
    now = datetime.now()
    mes = now.strftime("%Y-%m")
    conn = get_conn()
    conn.execute("""
        INSERT INTO pagos (chofer_id, mes_pagado, confirmado_por)
        VALUES (?, ?, ?)
    """, (telegram_id, mes, confirmado_por))
    conn.execute("""
        UPDATE choferes SET estado='activo', fecha_pago=? WHERE telegram_id=?
    """, (now.strftime("%Y-%m-%d"), telegram_id))
    conn.commit()
    conn.close()


def get_choferes_pendientes():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM choferes WHERE estado='pendiente'").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_choferes_activos_por_provincia(provincia: str):
    """Devuelve todos los choferes activos de una provincia para notificarles un viaje"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM choferes
        WHERE estado='activo' AND provincia=?
    """, (provincia,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_choferes_cuota_vencida():
    """Choferes activos cuyo pago tiene más de 30 días"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM choferes
        WHERE estado='activo'
        AND (fecha_pago IS NULL OR
             julianday('now') - julianday(fecha_pago) > 30)
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_rating_chofer(chofer_id, nueva_valoracion):
    conn = get_conn()
    chofer = dict(conn.execute("SELECT rating, viajes_total FROM choferes WHERE telegram_id=?",
                               (chofer_id,)).fetchone())
    total = chofer['viajes_total']
    rating_actual = chofer['rating']
    nuevo_rating = ((rating_actual * total) + nueva_valoracion) / (total + 1) if total > 0 else nueva_valoracion
    conn.execute("""
        UPDATE choferes SET rating=?, viajes_total=viajes_total+1 WHERE telegram_id=?
    """, (round(nuevo_rating, 2), chofer_id))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# FUNCIONES DE CLIENTES
# ──────────────────────────────────────────────

def registrar_cliente(telegram_id, username, telefono=None, provincia=None):
    conn = get_conn()
    conn.execute("""
        INSERT OR IGNORE INTO clientes (telegram_id, username, telefono, provincia)
        VALUES (?, ?, ?, ?)
    """, (telegram_id, username, telefono, provincia))
    conn.commit()
    conn.close()


def get_cliente(telegram_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM clientes WHERE telegram_id=?", (telegram_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_cliente(telegram_id, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    conn = get_conn()
    conn.execute(f"UPDATE clientes SET {sets} WHERE telegram_id=?",
                 (*kwargs.values(), telegram_id))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
# FUNCIONES DE VIAJES
# ──────────────────────────────────────────────

def crear_viaje(cliente_id, provincia, municipio_origen, direccion_origen,
                destino, pasajeros, equipaje, precio_oferta):
    conn = get_conn()
    cursor = conn.execute("""
        INSERT INTO viajes
        (cliente_id, provincia, municipio_origen, direccion_origen,
         destino, pasajeros, equipaje, precio_oferta, estado)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'publicado')
    """, (cliente_id, provincia, municipio_origen, direccion_origen,
          destino, pasajeros, equipaje, precio_oferta))
    viaje_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return viaje_id


def get_viaje(viaje_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM viajes WHERE id=?", (viaje_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def actualizar_viaje(viaje_id, **kwargs):
    if not kwargs:
        return
    sets = ", ".join(f"{k}=?" for k in kwargs)
    conn = get_conn()
    conn.execute(f"UPDATE viajes SET {sets} WHERE id=?",
                 (*kwargs.values(), viaje_id))
    conn.commit()
    conn.close()


def cliente_tiene_viaje_activo(cliente_id):
    conn = get_conn()
    row = conn.execute("""
        SELECT id FROM viajes
        WHERE cliente_id=? AND estado IN ('publicado','aceptado')
    """, (cliente_id,)).fetchone()
    conn.close()
    return row is not None


def get_viajes_expirados():
    """Viajes publicados hace más de 30 minutos sin chofer"""
    conn = get_conn()
    rows = conn.execute("""
        SELECT * FROM viajes
        WHERE estado='publicado'
        AND (julianday('now') - julianday(fecha_creacion)) * 1440 > 30
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_estadisticas():
    conn = get_conn()
    stats = {}
    stats['choferes_activos'] = conn.execute(
        "SELECT COUNT(*) FROM choferes WHERE estado='activo'").fetchone()[0]
    stats['choferes_pendientes'] = conn.execute(
        "SELECT COUNT(*) FROM choferes WHERE estado='pendiente'").fetchone()[0]
    stats['viajes_hoy'] = conn.execute(
        "SELECT COUNT(*) FROM viajes WHERE date(fecha_creacion)=date('now')").fetchone()[0]
    stats['viajes_mes'] = conn.execute(
        "SELECT COUNT(*) FROM viajes WHERE strftime('%Y-%m',fecha_creacion)=strftime('%Y-%m','now')").fetchone()[0]
    stats['ingresos_mes'] = conn.execute(
        "SELECT COUNT(*)*250 FROM pagos WHERE strftime('%Y-%m',fecha_pago)=strftime('%Y-%m','now')").fetchone()[0]
    conn.close()
    return stats


def aprobar_chofer(telegram_id: int):
    """Aprueba chofer pero lo deja en pendiente_pago hasta que pague"""
    conn = get_conn()
    conn.execute("""
        UPDATE choferes SET estado='pendiente_pago'
        WHERE telegram_id=?
    """, (telegram_id,))
    conn.commit()
    conn.close()


def rechazar_chofer(telegram_id: int):
    conn = get_conn()
    conn.execute("UPDATE choferes SET estado='rechazado' WHERE telegram_id=?", (telegram_id,))
    conn.commit()
    conn.close()


def confirmar_pago_chofer(telegram_id: int):
    """Confirma pago y activa chofer por 30 dias"""
    from datetime import datetime
    conn = get_conn()
    conn.execute("""
        UPDATE choferes SET estado='activo', fecha_pago=?
        WHERE telegram_id=?
    """, (datetime.now().isoformat(), telegram_id))
    conn.execute("""
        INSERT INTO pagos (chofer_id, monto, fecha_pago, mes_pagado, confirmado_por)
        VALUES (?, 250, ?, ?, 'admin')
    """, (telegram_id, datetime.now().isoformat(), datetime.now().strftime("%Y-%m")))
    conn.commit()
    conn.close()
