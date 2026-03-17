#!/bin/bash
# Script para executar todos os testes do WebSocket
# Task 17: Implementar WebSocket para real-time updates

echo "=========================================="
echo "Task 17 - WebSocket Tests"
echo "=========================================="
echo ""

# Cores para output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Função para executar testes
run_test() {
    local test_file=$1
    local test_name=$2
    
    echo -e "${YELLOW}Executando: ${test_name}${NC}"
    echo "----------------------------------------"
    
    if pytest "$test_file" -v --tb=short; then
        echo -e "${GREEN}✓ ${test_name} - PASSOU${NC}"
        echo ""
        return 0
    else
        echo -e "${RED}✗ ${test_name} - FALHOU${NC}"
        echo ""
        return 1
    fi
}

# Contador de testes
total_tests=0
passed_tests=0

# 1. Testes de Propriedade (Property 4: Channel Isolation)
echo "=========================================="
echo "1. Testes de Propriedade"
echo "=========================================="
total_tests=$((total_tests + 1))
if run_test "test_websocket_properties.py" "Property 4: WebSocket Channel Isolation"; then
    passed_tests=$((passed_tests + 1))
fi

# 2. Testes Unitários
echo "=========================================="
echo "2. Testes Unitários"
echo "=========================================="
total_tests=$((total_tests + 1))
if run_test "test_websocket_unit.py" "Testes Unitários WebSocket"; then
    passed_tests=$((passed_tests + 1))
fi

# Resumo
echo "=========================================="
echo "RESUMO DOS TESTES"
echo "=========================================="
echo "Total de suítes: $total_tests"
echo "Passou: $passed_tests"
echo "Falhou: $((total_tests - passed_tests))"
echo ""

if [ $passed_tests -eq $total_tests ]; then
    echo -e "${GREEN}✓ TODOS OS TESTES PASSARAM!${NC}"
    echo ""
    echo "Task 17 - WebSocket implementado com sucesso!"
    echo "Requisitos validados: 1.5, 38.1-38.8"
    exit 0
else
    echo -e "${RED}✗ ALGUNS TESTES FALHARAM${NC}"
    echo ""
    echo "Por favor, revise os erros acima."
    exit 1
fi
