# -*- coding: utf-8 -*-
"""
Configuração de Testes para Event Service
"""

import sys
import os

# Adiciona o diretório raiz ao PYTHONPATH
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
