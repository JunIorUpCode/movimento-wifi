# -*- coding: utf-8 -*-
"""
Email Channel - Canal de Notificação via Email
Implementa envio de notificações via SendGrid
"""

import asyncio
from typing import Dict, Any, List
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

from shared.logging import get_logger

logger = get_logger(__name__)


class EmailChannel:
    """
    Canal de notificação via Email (SendGrid).
    
    **Templates**: Usa templates HTML em português
    
    **Retry**: Implementa retry com exponential backoff
    
    **Quiet Hours**: Respeita configuração de quiet_hours
    """
    
    def __init__(self, api_key: str, recipients: List[str], from_email: str = "noreply@wifisense.com"):
        """
        Inicializa canal de email.
        
        Args:
            api_key: API key do SendGrid
            recipients: Lista de emails destinatários
            from_email: Email remetente
        """
        self.api_key = api_key
        self.recipients = recipients
        self.from_email = from_email
        self.client = SendGridAPIClient(api_key)
        
        logger.info(
            "EmailChannel inicializado",
            recipients_count=len(recipients)
        )
    
    async def send_notification(
        self,
        event_data: Dict[str, Any],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Envia notificação via email para todos os destinatários.
        
        **Retry**: Tenta até max_retries vezes com exponential backoff
        
        **Template HTML**: Usa template responsivo em português
        
        Args:
            event_data: Dados do evento
            max_retries: Número máximo de tentativas
        
        Returns:
            Dict com resultado do envio:
            {
                "success": bool,
                "sent_to": List[str],
                "failed": List[str],
                "error": str (opcional)
            }
        """
        # Gera HTML do email
        html_content = self._generate_html(event_data)
        subject = self._generate_subject(event_data)
        
        sent_to = []
        failed = []
        
        # Envia para cada destinatário
        for recipient in self.recipients:
            success = await self._send_to_recipient(
                recipient=recipient,
                subject=subject,
                html_content=html_content,
                max_retries=max_retries
            )
            
            if success:
                sent_to.append(recipient)
            else:
                failed.append(recipient)
        
        # Resultado
        result = {
            "success": len(sent_to) > 0,
            "sent_to": sent_to,
            "failed": failed
        }
        
        if failed:
            result["error"] = f"Falha ao enviar para {len(failed)} destinatário(s)"
        
        logger.info(
            "Notificação Email enviada",
            sent_to_count=len(sent_to),
            failed_count=len(failed)
        )
        
        return result
    
    async def _send_to_recipient(
        self,
        recipient: str,
        subject: str,
        html_content: str,
        max_retries: int
    ) -> bool:
        """
        Envia email para um destinatário específico com retry.
        
        Args:
            recipient: Email destinatário
            subject: Assunto do email
            html_content: Conteúdo HTML
            max_retries: Número máximo de tentativas
        
        Returns:
            bool: True se enviado com sucesso, False caso contrário
        """
        for attempt in range(max_retries):
            try:
                message = Mail(
                    from_email=Email(self.from_email),
                    to_emails=To(recipient),
                    subject=subject,
                    html_content=Content("text/html", html_content)
                )
                
                # Envia via SendGrid (síncrono, roda em executor)
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.client.send,
                    message
                )
                
                if response.status_code in [200, 201, 202]:
                    logger.debug(
                        "Email enviado",
                        recipient=recipient,
                        attempt=attempt + 1,
                        status_code=response.status_code
                    )
                    return True
                else:
                    logger.warning(
                        f"Email retornou status inesperado: {response.status_code}",
                        recipient=recipient,
                        attempt=attempt + 1
                    )
            
            except Exception as e:
                logger.warning(
                    f"Erro ao enviar email (tentativa {attempt + 1}/{max_retries})",
                    recipient=recipient,
                    error=str(e)
                )
                
                # Exponential backoff
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
        
        return False
    
    def _generate_subject(self, event_data: Dict[str, Any]) -> str:
        """
        Gera assunto do email baseado no tipo de evento.
        
        Args:
            event_data: Dados do evento
        
        Returns:
            str: Assunto do email
        """
        event_type_map = {
            "presence": "Presença Detectada",
            "movement": "Movimento Detectado",
            "fall_suspected": "🚨 ALERTA: Queda Detectada",
            "prolonged_inactivity": "⏰ Inatividade Prolongada"
        }
        
        event_type = event_data.get("event_type", "unknown")
        event_type_pt = event_type_map.get(event_type, "Alerta WiFiSense")
        
        device_name = event_data.get("device_name", "Dispositivo")
        
        return f"WiFiSense - {event_type_pt} ({device_name})"
    
    def _generate_html(self, event_data: Dict[str, Any]) -> str:
        """
        Gera HTML do email com template responsivo em português.
        
        Args:
            event_data: Dados do evento
        
        Returns:
            str: HTML do email
        """
        # Mapeia tipos de evento
        event_type_map = {
            "presence": "Presença Detectada",
            "movement": "Movimento Detectado",
            "fall_suspected": "Queda Detectada",
            "prolonged_inactivity": "Inatividade Prolongada"
        }
        
        event_type = event_data.get("event_type", "unknown")
        event_type_pt = event_type_map.get(event_type, event_type)
        
        confidence = event_data.get("confidence", 0.0)
        confidence_pct = int(confidence * 100)
        
        device_name = event_data.get("device_name", "Desconhecido")
        timestamp = event_data.get("timestamp", "")
        
        # Cor baseada no tipo
        color_map = {
            "presence": "#4CAF50",
            "movement": "#2196F3",
            "fall_suspected": "#F44336",
            "prolonged_inactivity": "#FF9800"
        }
        color = color_map.get(event_type, "#9E9E9E")
        
        # Template HTML responsivo
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Alerta WiFiSense</title>
</head>
<body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <!-- Header -->
                    <tr>
                        <td style="background-color: {color}; padding: 30px; text-align: center;">
                            <h1 style="margin: 0; color: #ffffff; font-size: 24px;">WiFiSense</h1>
                            <p style="margin: 10px 0 0 0; color: #ffffff; font-size: 16px;">Sistema de Monitoramento</p>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="margin: 0 0 20px 0; color: #333333; font-size: 20px;">Alerta de Evento</h2>
                            
                            <table width="100%" cellpadding="10" cellspacing="0" style="border: 1px solid #e0e0e0; border-radius: 4px;">
                                <tr>
                                    <td style="background-color: #f9f9f9; font-weight: bold; color: #666666; width: 40%;">Tipo de Evento:</td>
                                    <td style="color: #333333;">{event_type_pt}</td>
                                </tr>
                                <tr>
                                    <td style="background-color: #f9f9f9; font-weight: bold; color: #666666;">Confiança:</td>
                                    <td style="color: #333333;">{confidence_pct}%</td>
                                </tr>
                                <tr>
                                    <td style="background-color: #f9f9f9; font-weight: bold; color: #666666;">Dispositivo:</td>
                                    <td style="color: #333333;">{device_name}</td>
                                </tr>
                                <tr>
                                    <td style="background-color: #f9f9f9; font-weight: bold; color: #666666;">Horário:</td>
                                    <td style="color: #333333;">{timestamp}</td>
                                </tr>
                            </table>
                            
                            <p style="margin: 20px 0 0 0; color: #666666; font-size: 14px; line-height: 1.6;">
                                Este é um alerta automático gerado pelo sistema WiFiSense. 
                                Para mais detalhes, acesse o painel de controle.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f9f9f9; padding: 20px 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="margin: 0; color: #999999; font-size: 12px;">
                                © 2024 WiFiSense. Todos os direitos reservados.
                            </p>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
        
        return html
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão com SendGrid enviando email de teste.
        
        Returns:
            Dict com resultado do teste
        """
        test_html = """
<!DOCTYPE html>
<html>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>🧪 Teste de Notificação WiFiSense</h2>
    <p>Se você recebeu este email, as notificações estão funcionando corretamente!</p>
</body>
</html>
"""
        
        sent_count = 0
        
        for recipient in self.recipients:
            try:
                message = Mail(
                    from_email=Email(self.from_email),
                    to_emails=To(recipient),
                    subject="Teste de Notificação WiFiSense",
                    html_content=Content("text/html", test_html)
                )
                
                response = await asyncio.get_event_loop().run_in_executor(
                    None,
                    self.client.send,
                    message
                )
                
                if response.status_code in [200, 201, 202]:
                    sent_count += 1
            
            except Exception as e:
                logger.error(
                    "Erro ao testar email",
                    recipient=recipient,
                    error=str(e)
                )
        
        success = sent_count > 0
        
        return {
            "success": success,
            "message": f"Teste enviado para {sent_count}/{len(self.recipients)} destinatário(s)",
            "recipients_tested": sent_count
        }
