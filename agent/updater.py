# -*- coding: utf-8 -*-
"""
updater.py — Auto-update do WiFiSense Local Agent.

Verifica periodicamente novas versões no GitHub Releases,
baixa e aplica a atualização com rollback automático em caso de falha.

Uso:
    python updater.py --check          # apenas verifica, não atualiza
    python updater.py --update         # verifica e atualiza se disponível
    python updater.py --daemon 3600    # roda em loop a cada 3600s (padrão)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import time
import zipfile
from pathlib import Path
from typing import Optional
from urllib.request import urlopen, Request
from urllib.error import URLError

logger = logging.getLogger("wifisense.updater")

CURRENT_VERSION = "1.0.0"
GITHUB_RELEASES_API = "https://api.github.com/repos/wifisense/wifisense-local/releases/latest"
INSTALL_DIR = Path(os.environ.get("WIFISENSE_DIR", Path(__file__).parent))
BACKUP_DIR = INSTALL_DIR / ".update_backup"
UPDATE_INTERVAL_SECONDS = int(os.environ.get("UPDATE_INTERVAL", "3600"))


# ── Utilitários ───────────────────────────────────────────────────────────────

def _get_arch_tag() -> str:
    """Retorna tag de arquitetura para o release correto."""
    machine = platform.machine().lower()
    system = platform.system().lower()
    if system == "windows":
        return "windows-amd64"
    if "aarch64" in machine or "arm64" in machine:
        return "linux-arm64"
    if "armv7" in machine:
        return "linux-armv7"
    return "linux-amd64"


def _fetch_json(url: str, timeout: int = 10) -> dict:
    """Faz GET em uma URL e retorna o JSON parseado."""
    req = Request(url, headers={"User-Agent": f"WiFiSense/{CURRENT_VERSION}"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _sha256_file(path: Path) -> str:
    """Calcula SHA-256 de um arquivo."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _download_file(url: str, dest: Path, expected_sha256: Optional[str] = None) -> None:
    """Baixa um arquivo e opcionalmente verifica o checksum."""
    req = Request(url, headers={"User-Agent": f"WiFiSense/{CURRENT_VERSION}"})
    with urlopen(req, timeout=60) as resp, dest.open("wb") as f:
        shutil.copyfileobj(resp, f)

    if expected_sha256:
        actual = _sha256_file(dest)
        if actual != expected_sha256:
            dest.unlink(missing_ok=True)
            raise ValueError(
                f"Checksum inválido: esperado {expected_sha256}, obtido {actual}"
            )


# ── Verificação de versão ────────────────────────────────────────────────────

class ReleaseInfo:
    """Informações de um release GitHub."""

    def __init__(self, data: dict) -> None:
        self.version: str = data["tag_name"].lstrip("v")
        self.release_notes: str = data.get("body", "")
        self.prerelease: bool = data.get("prerelease", False)
        assets: list[dict] = data.get("assets", [])
        arch = _get_arch_tag()
        self.download_url: Optional[str] = None
        self.checksum_url: Optional[str] = None
        for asset in assets:
            name: str = asset["name"]
            if arch in name and (name.endswith(".tar.gz") or name.endswith(".zip")):
                self.download_url = asset["browser_download_url"]
            if arch in name and name.endswith(".sha256"):
                self.checksum_url = asset["browser_download_url"]


def check_for_update(
    allow_prerelease: bool = False,
) -> Optional[ReleaseInfo]:
    """
    Consulta o GitHub Releases e retorna ReleaseInfo se há versão mais nova.

    Returns:
        ReleaseInfo se há atualização disponível, None caso contrário.
    """
    try:
        data = _fetch_json(GITHUB_RELEASES_API)
        release = ReleaseInfo(data)
        if release.prerelease and not allow_prerelease:
            logger.debug("Pre-release ignorado: %s", release.version)
            return None
        if _version_tuple(release.version) > _version_tuple(CURRENT_VERSION):
            logger.info("Nova versão disponível: %s (atual: %s)", release.version, CURRENT_VERSION)
            return release
        logger.debug("Sistema atualizado: v%s", CURRENT_VERSION)
        return None
    except URLError as exc:
        logger.warning("Sem acesso à internet para verificar atualizações: %s", exc)
        return None
    except Exception as exc:
        logger.error("Erro ao verificar atualizações: %s", exc)
        return None


def _version_tuple(version: str) -> tuple[int, ...]:
    """Converte '1.2.3' em (1, 2, 3) para comparação."""
    try:
        return tuple(int(x) for x in version.split("."))
    except ValueError:
        return (0,)


# ── Aplicação da atualização ─────────────────────────────────────────────────

def apply_update(release: ReleaseInfo) -> bool:
    """
    Baixa e aplica a atualização, com rollback automático em caso de falha.

    Returns:
        True se a atualização foi aplicada com sucesso.
    """
    if not release.download_url:
        logger.error("URL de download não encontrada no release.")
        return False

    tmp_dir = INSTALL_DIR / ".update_tmp"
    tmp_dir.mkdir(exist_ok=True)
    archive_path = tmp_dir / "release.tar.gz"

    try:
        # 1. Baixa checksum (opcional)
        expected_sha256: Optional[str] = None
        if release.checksum_url:
            checksum_path = tmp_dir / "release.sha256"
            _download_file(release.checksum_url, checksum_path)
            expected_sha256 = checksum_path.read_text().split()[0]

        # 2. Baixa o pacote
        logger.info("Baixando v%s de %s...", release.version, release.download_url)
        _download_file(release.download_url, archive_path, expected_sha256)

        # 3. Faz backup da instalação atual
        logger.info("Criando backup da instalação atual...")
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        shutil.copytree(INSTALL_DIR, BACKUP_DIR, ignore=shutil.ignore_patterns(
            ".update_tmp", ".update_backup", "data", "logs", ".env", ".venv"
        ))

        # 4. Extrai o arquivo
        logger.info("Extraindo arquivos...")
        if archive_path.suffix == ".gz":
            with tarfile.open(archive_path, "r:gz") as tf:
                tf.extractall(tmp_dir)
        else:
            with zipfile.ZipFile(archive_path) as zf:
                zf.extractall(tmp_dir)

        # 5. Copia novos arquivos (preserva data/, logs/, .env, .venv)
        extracted = next(
            (d for d in tmp_dir.iterdir() if d.is_dir() and d.name != "release.tar.gz"),
            tmp_dir,
        )
        for item in extracted.iterdir():
            dest = INSTALL_DIR / item.name
            if item.name in {"data", "logs", ".env", ".venv", ".update_backup", ".update_tmp"}:
                continue
            if dest.exists():
                shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
            shutil.move(str(item), str(dest))

        logger.info("Atualização aplicada com sucesso: v%s", release.version)

        # 6. Reinicia o serviço (systemd ou processo atual)
        _restart_service()
        return True

    except Exception as exc:
        logger.error("Falha na atualização: %s — iniciando rollback...", exc)
        _rollback()
        return False
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)


def _rollback() -> None:
    """Restaura o backup após falha na atualização."""
    if not BACKUP_DIR.exists():
        logger.error("Backup não encontrado — rollback impossível.")
        return
    try:
        for item in BACKUP_DIR.iterdir():
            dest = INSTALL_DIR / item.name
            if dest.exists():
                shutil.rmtree(dest) if dest.is_dir() else dest.unlink()
            shutil.copy2(str(item), str(dest))
        logger.info("Rollback concluído.")
    except Exception as exc:
        logger.critical("Rollback falhou: %s", exc)


def _restart_service() -> None:
    """Tenta reiniciar o serviço systemd wifisense."""
    try:
        if platform.system() == "Linux":
            subprocess.run(
                ["systemctl", "restart", "wifisense.service"],
                check=True, capture_output=True,
            )
            logger.info("Serviço reiniciado via systemctl.")
        elif platform.system() == "Windows":
            subprocess.run(
                ["sc", "stop", "WiFiSenseSvc"],
                check=False, capture_output=True,
            )
            time.sleep(2)
            subprocess.run(
                ["sc", "start", "WiFiSenseSvc"],
                check=False, capture_output=True,
            )
            logger.info("Serviço reiniciado via sc.exe.")
    except Exception as exc:
        logger.warning("Não foi possível reiniciar automaticamente: %s", exc)
        logger.warning("Reinicie manualmente: systemctl restart wifisense")


# ── Daemon de update ─────────────────────────────────────────────────────────

def run_daemon(interval: int = UPDATE_INTERVAL_SECONDS) -> None:
    """Loop de verificação periódica de atualizações."""
    logger.info("Updater daemon iniciado. Intervalo: %ds", interval)
    while True:
        release = check_for_update()
        if release:
            apply_update(release)
        time.sleep(interval)


# ── Ponto de entrada ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    parser = argparse.ArgumentParser(description="WiFiSense Auto-Updater")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="Verifica se há atualização disponível")
    group.add_argument("--update", action="store_true", help="Verifica e aplica atualização")
    group.add_argument("--daemon", metavar="SECONDS", type=int, nargs="?",
                       const=UPDATE_INTERVAL_SECONDS,
                       help=f"Roda em daemon com intervalo (padrão: {UPDATE_INTERVAL_SECONDS}s)")
    args = parser.parse_args()

    if args.check:
        release = check_for_update()
        if release:
            print(f"Atualização disponível: v{release.version}")
            print(f"Notas: {release.release_notes[:200]}")
            sys.exit(0)
        else:
            print(f"Sistema atualizado: v{CURRENT_VERSION}")
            sys.exit(0)

    elif args.update:
        release = check_for_update()
        if release:
            success = apply_update(release)
            sys.exit(0 if success else 1)
        else:
            print(f"Nenhuma atualização disponível (atual: v{CURRENT_VERSION}).")
            sys.exit(0)

    else:
        interval = args.daemon if args.daemon is not None else UPDATE_INTERVAL_SECONDS
        run_daemon(interval)
