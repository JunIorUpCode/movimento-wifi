Name:           wifisense-local
Version:        1.0.0
Release:        1%{?dist}
Summary:        Detecção de presença via sinais Wi-Fi sem câmeras
License:        Proprietary
URL:            https://wifisense.com
BuildArch:      x86_64

Requires:       python3 >= 3.11
Requires:       python3-pip
Requires:       openssl

%description
WiFiSense Local é um sistema de monitoramento de presença e detecção
de quedas utilizando análise de sinais Wi-Fi (RSSI/CSI), sem necessidade
de câmeras. Inclui backend FastAPI, modelo ML (RandomForest) e dashboard web.

%install
rm -rf %{buildroot}
mkdir -p %{buildroot}/opt/wifisense
mkdir -p %{buildroot}/etc/systemd/system

# Copia arquivos (executado após o build extrair os fontes)
cp -r %{_sourcedir}/backend/app       %{buildroot}/opt/wifisense/
cp -r %{_sourcedir}/backend/models    %{buildroot}/opt/wifisense/
cp    %{_sourcedir}/backend/requirements.txt %{buildroot}/opt/wifisense/
cp -r %{_sourcedir}/shared            %{buildroot}/opt/wifisense/shared
cp    %{_sourcedir}/installers/linux/deb/etc/systemd/system/wifisense.service \
      %{buildroot}/etc/systemd/system/

%pre
# Cria usuário de serviço
getent passwd wifisense > /dev/null || \
    useradd --system --no-create-home --shell /sbin/nologin wifisense

%post
# Instala dependências e inicia serviço
pip3 install -r /opt/wifisense/requirements.txt --quiet 2>/dev/null || true
chown -R wifisense:wifisense /opt/wifisense

systemctl daemon-reload
systemctl enable wifisense.service
systemctl start wifisense.service
echo "WiFiSense Local iniciado. Acesse: http://localhost:8000"

%preun
systemctl stop wifisense.service 2>/dev/null || true
systemctl disable wifisense.service 2>/dev/null || true

%postun
systemctl daemon-reload

%files
/opt/wifisense/
/etc/systemd/system/wifisense.service

%changelog
* Tue Mar 17 2026 WiFiSense <contato@wifisense.com> - 1.0.0-1
- Versão inicial do pacote RPM
