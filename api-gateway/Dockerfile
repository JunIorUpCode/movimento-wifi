# ============================================================================
# WiFiSense SaaS - API Gateway Dockerfile
# ============================================================================
# Container Nginx para API Gateway com SSL e rate limiting
# ============================================================================

FROM nginx:1.25-alpine

# Instalar dependências necessárias
RUN apk add --no-cache \
    openssl \
    curl \
    bash

# Criar diretório para certificados SSL
RUN mkdir -p /etc/nginx/ssl

# Gerar certificado SSL auto-assinado para desenvolvimento
# Em produção, usar certificados Let's Encrypt
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/key.pem \
    -out /etc/nginx/ssl/cert.pem \
    -subj "/C=BR/ST=SP/L=SaoPaulo/O=WiFiSense/CN=api.wifisense.local"

# Copiar configurações do Nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY proxy_params.conf /etc/nginx/proxy_params.conf

# Criar diretórios de log
RUN mkdir -p /var/log/nginx

# Expor portas HTTP e HTTPS
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

# Comando para iniciar o Nginx
CMD ["nginx", "-g", "daemon off;"]
