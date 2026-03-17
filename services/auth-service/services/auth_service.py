# -*- coding: utf-8 -*-
"""
Auth Service - Lógica de negócio de autenticação
Gerencia registro, login, e bloqueio de contas
"""

from datetime import datetime, timedelta
from typing import Optional
import bcrypt
import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User, PlanType, TenantStatus
from services.jwt_service import jwt_service
from shared.config import settings
from shared.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """
    Serviço de autenticação e gerenciamento de usuários
    Implementa registro, login, e segurança de contas
    """
    
    def __init__(self):
        """Inicializa o serviço de autenticação"""
        self.redis_client: Optional[redis.Redis] = None
        self.bcrypt_rounds = 12  # Requisito 19.3
        self.max_login_attempts = 5  # Requisito 19.6
        self.lockout_window_minutes = 15  # Requisito 19.6
        self.lockout_duration_minutes = 30  # Requisito 19.6
    
    async def initialize(self):
        """Conecta ao Redis para rastreamento de tentativas de login"""
        if self.redis_client is None:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            logger.info("AuthService conectado ao Redis")
    
    async def close(self):
        """Fecha conexão com Redis"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("AuthService desconectado do Redis")
    
    def hash_password(self, password: str) -> str:
        """
        Gera hash bcrypt da senha com 12 rounds
        
        Args:
            password: Senha em texto plano
        
        Returns:
            Hash bcrypt da senha
        
        Requisitos: 19.3
        """
        # Gera salt e hash com 12 rounds
        salt = bcrypt.gensalt(rounds=self.bcrypt_rounds)
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        
        return password_hash.decode('utf-8')
    
    def verify_password(self, password: str, password_hash: str) -> bool:
        """
        Verifica se senha corresponde ao hash
        
        Args:
            password: Senha em texto plano
            password_hash: Hash bcrypt armazenado
        
        Returns:
            True se senha correta, False caso contrário
        """
        return bcrypt.checkpw(
            password.encode('utf-8'),
            password_hash.encode('utf-8')
        )
    
    async def register_tenant(
        self,
        email: str,
        password: str,
        name: str,
        plan_type: PlanType,
        session: AsyncSession
    ) -> User:
        """
        Registra um novo tenant no sistema
        
        Args:
            email: Email do tenant
            password: Senha em texto plano
            name: Nome do tenant
            plan_type: Tipo de plano (basic ou premium)
            session: Sessão do banco de dados
        
        Returns:
            Usuário criado
        
        Raises:
            ValueError: Se email já existe
        
        Requisitos: 19.3
        """
        # Verifica se email já existe
        result = await session.execute(
            select(User).where(User.email == email)
        )
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            logger.warning(f"Tentativa de registro com email duplicado: {email}")
            raise ValueError("Email já cadastrado")
        
        # Hash da senha com bcrypt (12 rounds)
        password_hash = self.hash_password(password)
        
        # Cria novo usuário com período de trial de 7 dias
        trial_ends_at = datetime.utcnow() + timedelta(days=7)
        
        user = User(
            email=email,
            password_hash=password_hash,
            name=name,
            plan_type=plan_type,
            status=TenantStatus.TRIAL,
            trial_ends_at=trial_ends_at
        )
        
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
        logger.info(
            f"Novo tenant registrado: {email}",
            tenant_id=str(user.id),
            email=email,
            plan_type=plan_type.value,
            trial_ends_at=trial_ends_at.isoformat()
        )
        
        return user
    
    async def check_account_lockout(self, email: str) -> tuple[bool, Optional[int]]:
        """
        Verifica se conta está bloqueada por tentativas de login falhadas
        
        Args:
            email: Email do usuário
        
        Returns:
            Tupla (bloqueado, segundos_restantes)
        
        Requisitos: 19.6, 19.7
        """
        if not self.redis_client:
            await self.initialize()
        
        lockout_key = f"lockout:{email}"
        
        # Verifica se conta está bloqueada
        lockout_until = await self.redis_client.get(lockout_key)
        
        if lockout_until:
            lockout_time = datetime.fromisoformat(lockout_until)
            now = datetime.utcnow()
            
            if now < lockout_time:
                seconds_remaining = int((lockout_time - now).total_seconds())
                logger.warning(
                    f"Conta bloqueada: {email}",
                    email=email,
                    seconds_remaining=seconds_remaining
                )
                return True, seconds_remaining
            else:
                # Lockout expirou, remove chave
                await self.redis_client.delete(lockout_key)
        
        return False, None
    
    async def record_failed_login(self, email: str):
        """
        Registra tentativa de login falhada e bloqueia conta se necessário
        
        Args:
            email: Email do usuário
        
        Requisitos: 19.6, 19.7
        """
        if not self.redis_client:
            await self.initialize()
        
        attempts_key = f"login_attempts:{email}"
        lockout_key = f"lockout:{email}"
        
        # Incrementa contador de tentativas
        attempts = await self.redis_client.incr(attempts_key)
        
        # Define TTL de 15 minutos na primeira tentativa
        if attempts == 1:
            await self.redis_client.expire(attempts_key, self.lockout_window_minutes * 60)
        
        logger.warning(
            f"Tentativa de login falhada: {email}",
            email=email,
            attempts=attempts,
            max_attempts=self.max_login_attempts
        )
        
        # Se atingiu 5 tentativas, bloqueia conta por 30 minutos
        if attempts >= self.max_login_attempts:
            lockout_until = datetime.utcnow() + timedelta(minutes=self.lockout_duration_minutes)
            await self.redis_client.setex(
                lockout_key,
                self.lockout_duration_minutes * 60,
                lockout_until.isoformat()
            )
            
            # Limpa contador de tentativas
            await self.redis_client.delete(attempts_key)
            
            logger.error(
                f"Conta bloqueada por excesso de tentativas: {email}",
                email=email,
                lockout_until=lockout_until.isoformat()
            )
    
    async def clear_failed_login_attempts(self, email: str):
        """
        Limpa contador de tentativas de login após sucesso
        
        Args:
            email: Email do usuário
        """
        if not self.redis_client:
            await self.initialize()
        
        attempts_key = f"login_attempts:{email}"
        await self.redis_client.delete(attempts_key)
    
    async def login(
        self,
        email: str,
        password: str,
        session: AsyncSession
    ) -> tuple[User, str]:
        """
        Autentica usuário e gera token JWT
        
        Args:
            email: Email do usuário
            password: Senha em texto plano
            session: Sessão do banco de dados
        
        Returns:
            Tupla (usuário, token_jwt)
        
        Raises:
            ValueError: Se credenciais inválidas ou conta bloqueada
        
        Requisitos: 19.3, 19.6, 19.7
        """
        # Verifica se conta está bloqueada
        is_locked, seconds_remaining = await self.check_account_lockout(email)
        
        if is_locked:
            raise ValueError(
                f"Conta bloqueada por excesso de tentativas. "
                f"Tente novamente em {seconds_remaining // 60} minutos."
            )
        
        # Busca usuário no banco
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        # Verifica se usuário existe e senha está correta
        if not user or not self.verify_password(password, user.password_hash):
            await self.record_failed_login(email)
            logger.warning(f"Login falhado: credenciais inválidas para {email}")
            raise ValueError("Email ou senha incorretos")
        
        # Verifica se conta está suspensa ou expirada
        if user.status in [TenantStatus.SUSPENDED, TenantStatus.EXPIRED]:
            logger.warning(
                f"Tentativa de login em conta {user.status.value}: {email}",
                email=email,
                status=user.status.value
            )
            raise ValueError(f"Conta {user.status.value}. Entre em contato com o suporte.")
        
        # Limpa tentativas de login falhadas
        await self.clear_failed_login_attempts(email)
        
        # Determina role baseado no email
        # Emails que terminam com @wifisense.com são admins
        role = "admin" if email.endswith("@wifisense.com") else "tenant"
        
        # Gera token JWT
        token = jwt_service.generate_jwt_token(
            tenant_id=str(user.id),
            email=user.email,
            role=role,
            plan=user.plan_type.value
        )
        
        logger.info(
            f"Login bem-sucedido: {email}",
            tenant_id=str(user.id),
            email=email,
            role=role,
            plan=user.plan_type.value
        )
        
        return user, token
    
    async def logout(self, token: str):
        """
        Invalida token JWT (adiciona à blacklist)
        
        Args:
            token: Token JWT a ser invalidado
        
        Requisitos: 19.2
        """
        if not self.redis_client:
            await self.initialize()
        
        # Decodifica token para obter expiração
        payload = jwt_service.validate_jwt_token(token)
        exp = payload.get("exp")
        
        if exp:
            # Adiciona token à blacklist até expiração
            ttl = exp - int(datetime.utcnow().timestamp())
            if ttl > 0:
                await self.redis_client.setex(
                    f"blacklist:{token}",
                    ttl,
                    "1"
                )
                
                logger.info(
                    "Token invalidado (logout)",
                    tenant_id=payload.get("sub"),
                    email=payload.get("email")
                )
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """
        Verifica se token está na blacklist
        
        Args:
            token: Token JWT
        
        Returns:
            True se token está invalidado, False caso contrário
        """
        if not self.redis_client:
            await self.initialize()
        
        return await self.redis_client.exists(f"blacklist:{token}") > 0


# Instância global do serviço de autenticação
auth_service = AuthService()
