# -*- coding: utf-8 -*-
"""
Cron Jobs - Tarefas Agendadas do Billing Service

Jobs:
1. Geração de faturas mensais (dia 1 às 00:00 UTC)
2. Retry de pagamentos falhados (diário às 02:00 UTC)

Requisitos: 17.2, 17.4, 17.5
"""

import asyncio
from datetime import datetime

from services.invoice_generator import InvoiceGenerator
from shared.database import get_billing_db
from shared.logging import get_logger

logger = get_logger(__name__)


async def generate_monthly_invoices_job():
    """
    Job de geração de faturas mensais
    
    Deve ser executado no dia 1 de cada mês às 00:00 UTC.
    Gera faturas para todos os tenants ativos.
    
    Requisito: 17.2
    """
    logger.info("Iniciando job de geração de faturas mensais")
    
    db_manager = get_billing_db()
    
    try:
        # Inicializa banco de dados
        await db_manager.initialize()
        
        # Obtém sessão do banco
        async with db_manager.get_session() as session:
            # Cria gerador de faturas
            invoice_generator = InvoiceGenerator(session)
            
            # Gera faturas
            stats = await invoice_generator.generate_monthly_invoices()
            
            logger.info(
                f"Job de geração de faturas concluído: {stats}",
                **stats
            )
            
            return stats
    
    except Exception as e:
        logger.error(
            f"Erro no job de geração de faturas: {str(e)}",
            error=str(e)
        )
        raise
    
    finally:
        await db_manager.close()


async def retry_failed_payments_job():
    """
    Job de retry de pagamentos falhados
    
    Deve ser executado diariamente às 02:00 UTC.
    Tenta novamente pagamentos que falharam há 3 dias.
    Suspende contas após 3 tentativas falhadas.
    
    Requisitos: 17.4, 17.5
    """
    logger.info("Iniciando job de retry de pagamentos falhados")
    
    db_manager = get_billing_db()
    
    try:
        # Inicializa banco de dados
        await db_manager.initialize()
        
        # Obtém sessão do banco
        async with db_manager.get_session() as session:
            # Cria gerador de faturas
            invoice_generator = InvoiceGenerator(session)
            
            # Executa retry
            stats = await invoice_generator.retry_failed_payments()
            
            logger.info(
                f"Job de retry de pagamentos concluído: {stats}",
                **stats
            )
            
            return stats
    
    except Exception as e:
        logger.error(
            f"Erro no job de retry de pagamentos: {str(e)}",
            error=str(e)
        )
        raise
    
    finally:
        await db_manager.close()


async def main():
    """
    Função principal para executar jobs manualmente
    
    Uso:
        python cron_jobs.py generate_invoices
        python cron_jobs.py retry_payments
    """
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python cron_jobs.py [generate_invoices|retry_payments]")
        sys.exit(1)
    
    job_name = sys.argv[1]
    
    if job_name == "generate_invoices":
        await generate_monthly_invoices_job()
    elif job_name == "retry_payments":
        await retry_failed_payments_job()
    else:
        print(f"Job desconhecido: {job_name}")
        print("Jobs disponíveis: generate_invoices, retry_payments")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
