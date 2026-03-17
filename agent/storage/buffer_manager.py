# -*- coding: utf-8 -*-
"""
Gerenciador de Buffer Local
Armazena dados em SQLite durante offline e gerencia upload quando online
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime


class BufferManager:
    """
    Gerenciador de buffer local usando SQLite.
    Armazena dados durante offline e gerencia upload quando conexão é restaurada.
    """
    
    def __init__(
        self,
        db_path: str = "agent_buffer.db",
        max_size_mb: int = 100,
        config_dir: Optional[Path] = None
    ):
        """
        Inicializa o gerenciador de buffer.
        
        Args:
            db_path: Caminho do arquivo SQLite
            max_size_mb: Tamanho máximo do buffer em MB
            config_dir: Diretório para armazenar o buffer (se None, usa ~/.wifisense_agent/)
        """
        if config_dir is None:
            config_dir = Path.home() / ".wifisense_agent"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.config_dir / db_path
        self.max_size_bytes = max_size_mb * 1024 * 1024
        
        # Inicializa banco de dados
        self._init_database()
    
    def _init_database(self) -> None:
        """Inicializa o banco de dados SQLite com schema"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Tabela para armazenar dados buffered
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS buffered_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL NOT NULL,
                features TEXT NOT NULL,
                created_at REAL NOT NULL,
                uploaded INTEGER DEFAULT 0
            )
        """)
        
        # Índice para queries eficientes
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_uploaded 
            ON buffered_data(uploaded, created_at)
        """)
        
        conn.commit()
        conn.close()
        
        print(f"[BufferManager] Database inicializado: {self.db_path}")
    
    def add_data(self, features: Dict[str, Any]) -> bool:
        """
        Adiciona dados ao buffer.
        
        Args:
            features: Features extraídas do sinal
        
        Returns:
            bool: True se adicionado com sucesso, False se buffer cheio
        """
        # Verifica tamanho do buffer
        if self.get_buffer_size_bytes() >= self.max_size_bytes:
            # Remove dados mais antigos (FIFO)
            self._remove_oldest_data()
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            # Serializa features para JSON
            features_json = json.dumps(features, ensure_ascii=False)
            
            cursor.execute("""
                INSERT INTO buffered_data (timestamp, features, created_at)
                VALUES (?, ?, ?)
            """, (
                features.get('timestamp', datetime.now().timestamp()),
                features_json,
                datetime.now().timestamp()
            ))
            
            conn.commit()
            conn.close()
            
            return True
        
        except Exception as e:
            print(f"[BufferManager] Erro ao adicionar dados: {e}")
            return False
    
    def get_pending_data(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retorna dados pendentes de upload.
        
        Args:
            limit: Número máximo de registros a retornar
        
        Returns:
            List de dicionários com id e features
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, timestamp, features
                FROM buffered_data
                WHERE uploaded = 0
                ORDER BY created_at ASC
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            # Deserializa features
            result = []
            for row in rows:
                result.append({
                    'id': row[0],
                    'timestamp': row[1],
                    'features': json.loads(row[2])
                })
            
            return result
        
        except Exception as e:
            print(f"[BufferManager] Erro ao buscar dados pendentes: {e}")
            return []
    
    def mark_as_uploaded(self, record_ids: List[int]) -> None:
        """
        Marca registros como uploaded.
        
        Args:
            record_ids: Lista de IDs dos registros
        """
        if not record_ids:
            return
        
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            placeholders = ','.join('?' * len(record_ids))
            cursor.execute(f"""
                UPDATE buffered_data
                SET uploaded = 1
                WHERE id IN ({placeholders})
            """, record_ids)
            
            conn.commit()
            conn.close()
        
        except Exception as e:
            print(f"[BufferManager] Erro ao marcar como uploaded: {e}")
    
    def clear_uploaded_data(self) -> int:
        """
        Remove dados já uploaded do buffer.
        
        Returns:
            int: Número de registros removidos
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM buffered_data WHERE uploaded = 1")
            deleted = cursor.rowcount
            
            conn.commit()
            conn.close()
            
            # Vacuum para liberar espaço
            if deleted > 0:
                conn = sqlite3.connect(str(self.db_path))
                conn.execute("VACUUM")
                conn.close()
            
            return deleted
        
        except Exception as e:
            print(f"[BufferManager] Erro ao limpar dados uploaded: {e}")
            return 0
    
    def _remove_oldest_data(self, count: int = 100) -> None:
        """
        Remove os dados mais antigos (FIFO) quando buffer está cheio.
        
        Args:
            count: Número de registros a remover
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM buffered_data
                WHERE id IN (
                    SELECT id FROM buffered_data
                    ORDER BY created_at ASC
                    LIMIT ?
                )
            """, (count,))
            
            conn.commit()
            conn.close()
            
            print(f"[BufferManager] Removidos {count} registros mais antigos (buffer cheio)")
        
        except Exception as e:
            print(f"[BufferManager] Erro ao remover dados antigos: {e}")
    
    def get_buffer_size_bytes(self) -> int:
        """
        Retorna o tamanho atual do buffer em bytes.
        
        Returns:
            int: Tamanho do arquivo SQLite em bytes
        """
        if not self.db_path.exists():
            return 0
        return self.db_path.stat().st_size
    
    def get_buffer_size_mb(self) -> float:
        """
        Retorna o tamanho atual do buffer em MB.
        
        Returns:
            float: Tamanho do buffer em MB
        """
        return self.get_buffer_size_bytes() / (1024 * 1024)
    
    def get_pending_count(self) -> int:
        """
        Retorna o número de registros pendentes de upload.
        
        Returns:
            int: Número de registros pendentes
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM buffered_data WHERE uploaded = 0")
            count = cursor.fetchone()[0]
            
            conn.close()
            return count
        
        except Exception as e:
            print(f"[BufferManager] Erro ao contar pendentes: {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do buffer.
        
        Returns:
            Dict com estatísticas: size_mb, pending_count, uploaded_count
        """
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM buffered_data WHERE uploaded = 0")
            pending = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM buffered_data WHERE uploaded = 1")
            uploaded = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'size_mb': self.get_buffer_size_mb(),
                'pending_count': pending,
                'uploaded_count': uploaded,
                'max_size_mb': self.max_size_bytes / (1024 * 1024)
            }
        
        except Exception as e:
            print(f"[BufferManager] Erro ao obter estatísticas: {e}")
            return {
                'size_mb': 0,
                'pending_count': 0,
                'uploaded_count': 0,
                'max_size_mb': self.max_size_bytes / (1024 * 1024)
            }
