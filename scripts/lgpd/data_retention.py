#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data_retention.py — Conformidade LGPD: retenção e exclusão de dados pessoais.

Políticas implementadas:
  - Eventos de detecção: retidos por 90 dias (padrão)
  - Logs de notificação: retidos por 30 dias
  - Dados de audit: retidos por 1 ano
  - Dados de usuário excluído: anonimizados imediatamente
  - Exportação de dados pessoais (direito de acesso — Art. 18 LGPD)
  - Exclusão de dados pessoais (direito ao esquecimento — Art. 18 LGPD)

Uso:
    python data_retention.py --purge               # executa purge com políticas padrão
    python data_retention.py --export <tenant_id>  # exporta dados do tenant
    python data_retention.py --delete <user_id>    # anonimiza dados do usuário
    python data_retention.py --report              # relatório de dados armazenados
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# Configuração de conexão (lida do ambiente ou .env)
DB_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://wifisense:wifisense_password@localhost:5432/wifisense_saas",
)

# Políticas de retenção (em dias)
RETENTION_POLICIES: dict[str, int] = {
    "events":              int(os.environ.get("RETENTION_EVENTS_DAYS", "90")),
    "notification_logs":   int(os.environ.get("RETENTION_NOTIF_DAYS", "30")),
    "audit_logs":          int(os.environ.get("RETENTION_AUDIT_DAYS", "365")),
    "ml_training_data":    int(os.environ.get("RETENTION_ML_DAYS", "180")),
    "performance_metrics": int(os.environ.get("RETENTION_METRICS_DAYS", "60")),
}

LOG_FILE = Path(os.environ.get("LGPD_LOG", "logs/lgpd_operations.jsonl"))


def _log_operation(operation: str, details: dict) -> None:
    """Registra operação LGPD em log auditável (JSONL)."""
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "operation": operation,
        **details,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"[LGPD] {operation}: {details}")


def _get_connection():
    """Retorna conexão psycopg2. Lazy import para não exigir o driver em imports."""
    try:
        import psycopg2  # type: ignore[import-untyped]
        return psycopg2.connect(DB_URL)
    except ImportError:
        print("ERRO: psycopg2 não instalado. Execute: pip install psycopg2-binary")
        sys.exit(1)
    except Exception as exc:
        print(f"ERRO ao conectar ao banco: {exc}")
        sys.exit(1)


# ── Purge de dados expirados ─────────────────────────────────────────────────

def run_purge(dry_run: bool = False) -> dict[str, int]:
    """
    Remove registros que excederam o período de retenção.

    Args:
        dry_run: Se True, apenas conta os registros sem excluir.

    Returns:
        Dict com contagem de registros afetados por tabela.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    results: dict[str, int] = {}
    now = datetime.utcnow()

    queries = {
        "events": (
            "DELETE FROM events WHERE detected_at < %s",
            now - timedelta(days=RETENTION_POLICIES["events"]),
        ),
        "notification_logs": (
            "DELETE FROM notification_logs WHERE sent_at < %s",
            now - timedelta(days=RETENTION_POLICIES["notification_logs"]),
        ),
        "audit_logs": (
            "DELETE FROM audit_logs WHERE created_at < %s",
            now - timedelta(days=RETENTION_POLICIES["audit_logs"]),
        ),
        "performance_metrics": (
            "DELETE FROM performance_metrics WHERE recorded_at < %s",
            now - timedelta(days=RETENTION_POLICIES["performance_metrics"]),
        ),
    }

    for table, (delete_sql, cutoff) in queries.items():
        try:
            if dry_run:
                count_sql = delete_sql.replace("DELETE FROM", "SELECT COUNT(*) FROM", 1)
                cursor.execute(count_sql, (cutoff,))
                count = cursor.fetchone()[0]
            else:
                cursor.execute(delete_sql, (cutoff,))
                count = cursor.rowcount
            results[table] = count
        except Exception as exc:
            print(f"[LGPD] AVISO: falha na tabela {table}: {exc}")
            results[table] = -1

    if not dry_run:
        conn.commit()
        _log_operation("PURGE", {"tables": results, "dry_run": False})
    else:
        print("[LGPD] Dry-run — nenhum dado foi excluído.")

    cursor.close()
    conn.close()
    return results


# ── Exportação de dados (Art. 18 LGPD) ──────────────────────────────────────

def export_user_data(tenant_id: str, user_id: Optional[str] = None) -> dict:
    """
    Exporta todos os dados pessoais de um tenant/usuário (portabilidade).

    Returns:
        Dict com todos os dados encontrados, pronto para serializar em JSON.
    """
    conn = _get_connection()
    cursor = conn.cursor()
    export: dict = {"tenant_id": tenant_id, "exported_at": datetime.utcnow().isoformat(), "data": {}}

    # Eventos de detecção do tenant
    try:
        cursor.execute(
            "SELECT id, event_type, confidence, detected_at, device_id FROM events WHERE tenant_id = %s ORDER BY detected_at DESC LIMIT 1000",
            (tenant_id,),
        )
        rows = cursor.fetchall()
        export["data"]["events"] = [
            {"id": r[0], "type": r[1], "confidence": float(r[2]), "at": r[3].isoformat(), "device": r[4]}
            for r in rows
        ]
    except Exception as exc:
        export["data"]["events"] = {"error": str(exc)}

    # Logs de notificação
    try:
        cursor.execute(
            "SELECT id, channel, status, sent_at FROM notification_logs WHERE tenant_id = %s ORDER BY sent_at DESC LIMIT 500",
            (tenant_id,),
        )
        rows = cursor.fetchall()
        export["data"]["notification_logs"] = [
            {"id": r[0], "channel": r[1], "status": r[2], "at": r[3].isoformat()}
            for r in rows
        ]
    except Exception as exc:
        export["data"]["notification_logs"] = {"error": str(exc)}

    cursor.close()
    conn.close()

    _log_operation("EXPORT", {"tenant_id": tenant_id, "user_id": user_id, "records": sum(
        len(v) for v in export["data"].values() if isinstance(v, list)
    )})
    return export


# ── Exclusão/Anonimização (Art. 18 LGPD) ────────────────────────────────────

def delete_user_data(user_id: str, tenant_id: Optional[str] = None) -> dict[str, int]:
    """
    Anonimiza dados pessoais de um usuário excluído (direito ao esquecimento).

    - E-mails → hash SHA-256
    - Nomes → "usuário_excluído"
    - Tokens → NULL
    - Dados de presença: mantidos sem identificação (interesse legítimo de segurança)
    """
    import hashlib
    conn = _get_connection()
    cursor = conn.cursor()
    results: dict[str, int] = {}

    # Anonimiza usuário na tabela de usuários
    try:
        email_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        cursor.execute(
            """UPDATE users SET
               email = %s,
               name = 'usuario_excluido',
               phone = NULL,
               password_hash = 'DELETED',
               deleted_at = NOW()
               WHERE id = %s""",
            (f"deleted_{email_hash}@removed.invalid", user_id),
        )
        results["users"] = cursor.rowcount
    except Exception as exc:
        print(f"[LGPD] AVISO: falha ao anonimizar users: {exc}")
        results["users"] = -1

    # Revoga tokens de sessão
    try:
        cursor.execute("DELETE FROM user_sessions WHERE user_id = %s", (user_id,))
        results["sessions"] = cursor.rowcount
    except Exception:
        results["sessions"] = 0

    conn.commit()
    cursor.close()
    conn.close()

    _log_operation("DELETE_USER", {"user_id": user_id, "tenant_id": tenant_id, "tables": results})
    return results


# ── Relatório de dados armazenados ────────────────────────────────────────────

def generate_report() -> None:
    """Imprime relatório com volume de dados por tabela e datas limites."""
    conn = _get_connection()
    cursor = conn.cursor()
    now = datetime.utcnow()

    print("\n═══════════════════════════════════════════════════")
    print("  WiFiSense — Relatório LGPD de Dados Pessoais")
    print(f"  Gerado em: {now.isoformat()}")
    print("═══════════════════════════════════════════════════\n")

    checks = [
        ("Eventos de detecção", "events", "detected_at", RETENTION_POLICIES["events"]),
        ("Logs de notificação", "notification_logs", "sent_at", RETENTION_POLICIES["notification_logs"]),
        ("Logs de auditoria",   "audit_logs",         "created_at", RETENTION_POLICIES["audit_logs"]),
    ]

    for label, table, col, retention in checks:
        try:
            cursor.execute(f"SELECT COUNT(*), MIN({col}), MAX({col}) FROM {table}")
            count, oldest, newest = cursor.fetchone()
            expiry = now - timedelta(days=retention)
            cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {col} < %s", (expiry,))
            expired = cursor.fetchone()[0]
            print(f"  {label}")
            print(f"    Total: {count:,} registros")
            print(f"    Mais antigo: {oldest}")
            print(f"    Mais recente: {newest}")
            print(f"    Retenção: {retention} dias (limite: {expiry.date()})")
            print(f"    Prontos para purge: {expired:,} registros")
            print()
        except Exception as exc:
            print(f"  {label}: ERRO — {exc}\n")

    print("  Políticas de retenção configuradas:")
    for k, v in RETENTION_POLICIES.items():
        print(f"    {k}: {v} dias")
    print()

    cursor.close()
    conn.close()


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="WiFiSense LGPD — Gerenciamento de dados pessoais")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--purge",  action="store_true", help="Remove dados expirados conforme política de retenção")
    group.add_argument("--export", metavar="TENANT_ID",  help="Exporta dados pessoais do tenant (JSON)")
    group.add_argument("--delete", metavar="USER_ID",    help="Anonimiza dados do usuário (direito ao esquecimento)")
    group.add_argument("--report", action="store_true",  help="Exibe relatório de dados armazenados")
    parser.add_argument("--dry-run", action="store_true", help="Simula operação sem modificar dados (--purge)")
    parser.add_argument("--output",  metavar="FILE",      help="Salva exportação em arquivo JSON (--export)")
    args = parser.parse_args()

    if args.purge:
        results = run_purge(dry_run=args.dry_run)
        print("\nResultado do purge:")
        for table, count in results.items():
            action = "encontrados" if args.dry_run else "removidos"
            print(f"  {table}: {count} registros {action}")

    elif args.export:
        data = export_user_data(args.export)
        output = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
            print(f"Dados exportados para: {args.output}")
        else:
            print(output)

    elif args.delete:
        results = delete_user_data(args.delete)
        print(f"\nDados anonimizados para usuário {args.delete}:")
        for table, count in results.items():
            print(f"  {table}: {count} registros afetados")

    elif args.report:
        generate_report()
