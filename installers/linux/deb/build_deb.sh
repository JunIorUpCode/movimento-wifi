#!/bin/bash
# build_deb.sh — Gera pacote .deb para Ubuntu/Debian (amd64)
# Uso: bash installers/linux/deb/build_deb.sh

set -euo pipefail

VERSION="1.0.0"
PACKAGE="wifisense-local"
ARCH="amd64"
INSTALL_DIR="opt/wifisense"
BUILD_DIR="build/deb/${PACKAGE}_${VERSION}_${ARCH}"

echo "[1/5] Preparando estrutura do pacote..."
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/$INSTALL_DIR"
mkdir -p "$BUILD_DIR/etc/systemd/system"

echo "[2/5] Copiando arquivos do backend..."
cp -r backend/app          "$BUILD_DIR/$INSTALL_DIR/"
cp -r backend/models       "$BUILD_DIR/$INSTALL_DIR/"
cp    backend/requirements.txt "$BUILD_DIR/$INSTALL_DIR/"
cp -r shared               "$BUILD_DIR/$INSTALL_DIR/shared"

echo "[3/5] Copiando arquivos do pacote Debian..."
cp installers/linux/deb/DEBIAN/control  "$BUILD_DIR/DEBIAN/control"
cp installers/linux/deb/DEBIAN/postinst "$BUILD_DIR/DEBIAN/postinst"
cp installers/linux/deb/DEBIAN/prerm    "$BUILD_DIR/DEBIAN/prerm"
cp installers/linux/deb/etc/systemd/system/wifisense.service \
   "$BUILD_DIR/etc/systemd/system/"

chmod 755 "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/prerm"

echo "[4/5] Calculando tamanho instalado..."
INSTALLED_SIZE=$(du -sk "$BUILD_DIR/$INSTALL_DIR" | cut -f1)
sed -i "s/^Installed-Size:.*/Installed-Size: $INSTALLED_SIZE/" \
    "$BUILD_DIR/DEBIAN/control" 2>/dev/null || true

echo "[5/5] Construindo pacote .deb..."
mkdir -p dist
dpkg-deb --build --root-owner-group "$BUILD_DIR" \
    "dist/${PACKAGE}_${VERSION}_${ARCH}.deb"

echo ""
echo "Pacote gerado: dist/${PACKAGE}_${VERSION}_${ARCH}.deb"
echo "Para instalar: sudo dpkg -i dist/${PACKAGE}_${VERSION}_${ARCH}.deb"
