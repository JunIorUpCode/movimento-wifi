#!/bin/bash
# build_rpm.sh — Gera pacote .rpm para RHEL/CentOS/Fedora (x86_64)
# Requisito: rpm-build instalado (sudo dnf install rpm-build)
# Uso: bash installers/linux/rpm/build_rpm.sh

set -euo pipefail

VERSION="1.0.0"
RPM_BUILD_ROOT="$HOME/rpmbuild"

echo "[1/4] Preparando ambiente rpmbuild..."
mkdir -p "$RPM_BUILD_ROOT"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

echo "[2/4] Copiando spec e fontes..."
cp installers/linux/rpm/wifisense.spec "$RPM_BUILD_ROOT/SPECS/"
# Cria tarball dos fontes
tar czf "$RPM_BUILD_ROOT/SOURCES/wifisense-local-${VERSION}.tar.gz" \
    --transform "s,^,wifisense-local-${VERSION}/," \
    backend/app backend/models backend/requirements.txt \
    shared installers/linux/deb/etc

echo "[3/4] Construindo pacote RPM..."
rpmbuild -bb "$RPM_BUILD_ROOT/SPECS/wifisense.spec" \
    --define "_sourcedir $(pwd)" \
    --define "_topdir $RPM_BUILD_ROOT"

echo "[4/4] Copiando para dist/..."
mkdir -p dist
find "$RPM_BUILD_ROOT/RPMS" -name "*.rpm" -exec cp {} dist/ \;

echo ""
echo "Pacote RPM gerado em: dist/"
echo "Para instalar: sudo rpm -i dist/wifisense-local-${VERSION}-1.x86_64.rpm"
