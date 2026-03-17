# Testes de Propriedade - Agente Local WiFiSense

## Visão Geral

Este documento descreve os testes de propriedade implementados para o Agente Local usando Hypothesis, uma biblioteca de property-based testing para Python.

## O que são Testes de Propriedade?

Testes de propriedade (property-based tests) verificam que certas propriedades do sistema são verdadeiras para uma ampla gama de entradas geradas automaticamente. Ao invés de testar casos específicos, testamos propriedades universais que devem sempre ser verdadeiras.

## Propriedades Implementadas

### Property 15: Data Compression Before Transmission

**Arquivo:** `test_properties.py::TestDataCompression`

**Valida:** Requisito 8.4 - Compressão de dados antes da transmissão

**Descrição:** Verifica que o payload comprimido com gzip é menor que o payload original em JSON, garantindo economia de banda na transmissão de dados.

#### Testes Incluídos

1. **test_compressed_payload_smaller_than_original**
   - Gera 100 exemplos aleatórios de features (RSSI, variância, energia, etc.)
   - Verifica que compressão gzip reduz o tamanho do payload
   - Garante pelo menos 10% de redução no tamanho
   - Usa `assume()` para filtrar payloads muito pequenos (< 100 bytes) onde overhead do gzip pode aumentar o tamanho

2. **test_batch_compression_efficiency**
   - Gera batches de 10-100 amostras
   - Compara compressão em batch vs compressão individual
   - Verifica que batch compression é mais eficiente (economia >= 20%)
   - Demonstra benefício de enviar dados em lote

3. **test_http_client_compress_method**
   - Testa o método `_compress_data()` do HTTPClient
   - Verifica que dados podem ser comprimidos e descomprimidos corretamente
   - Garante preservação dos dados após compressão/descompressão

### Property 16: Offline Data Upload Round-Trip

**Arquivo:** `test_properties.py::TestBufferedDataUpload`

**Valida:** Requisito 8.7 - Upload de dados buffered durante offline

**Descrição:** Verifica que dados buffered localmente durante offline são uploaded corretamente quando a conexão é restaurada, preservando timestamps originais e ordem cronológica.

#### Testes Incluídos

1. **test_buffered_data_preserves_original_timestamps**
   - Gera 1-50 amostras com timestamps incrementais
   - Simula offline: buffer dados localmente no SQLite
   - Simula conexão restaurada: recupera dados do buffer
   - **PROPRIEDADE:** Timestamps originais devem ser preservados exatamente
   - Verifica que features também são preservadas corretamente
   - Testa marcação como uploaded e cleanup

2. **test_buffered_data_maintains_chronological_order**
   - Gera 5-20 amostras com timestamps conhecidos
   - Buffer dados e recupera do SQLite
   - **PROPRIEDADE:** Dados devem ser retornados em ordem cronológica
   - Verifica que todos os timestamps originais estão presentes
   - Garante que ordem temporal é mantida para análise correta

3. **test_buffer_survives_process_restart**
   - Cria primeira instância do BufferManager
   - Buffer dados e fecha a instância (simula crash/reinício)
   - Cria segunda instância apontando para o mesmo arquivo
   - **PROPRIEDADE:** Dados devem persistir entre reinicializações
   - Verifica que nenhum dado é perdido durante restart do processo

4. **test_buffer_fifo_when_full**
   - Cria buffer pequeno (1 MB) para testar overflow
   - Adiciona muitos dados até encher o buffer
   - **PROPRIEDADE:** Dados mais antigos devem ser descartados (FIFO)
   - Verifica que buffer não excede limite de tamanho
   - Garante que dados mais recentes são preservados

## Como Executar

### Executar todos os testes de propriedade

```bash
cd agent
python -m pytest test_properties.py -v
```

### Executar com estatísticas do Hypothesis

```bash
python -m pytest test_properties.py -v --hypothesis-show-statistics
```

### Executar apenas testes de compressão

```bash
python -m pytest test_properties.py::TestDataCompression -v
```

### Executar apenas testes de buffered data upload

```bash
python -m pytest test_properties.py::TestBufferedDataUpload -v
```

### Aumentar número de exemplos (mais rigoroso)

```bash
python -m pytest test_properties.py -v --hypothesis-max-examples=1000
```

## Resultados Esperados

```
test_properties.py::TestDataCompression::test_compressed_payload_smaller_than_original PASSED [ 14%]
test_properties.py::TestDataCompression::test_batch_compression_efficiency PASSED [ 28%]
test_properties.py::TestDataCompression::test_http_client_compress_method PASSED [ 42%]
test_properties.py::TestBufferedDataUpload::test_buffered_data_preserves_original_timestamps PASSED [ 57%]
test_properties.py::TestBufferedDataUpload::test_buffered_data_maintains_chronological_order PASSED [ 71%]
test_properties.py::TestBufferedDataUpload::test_buffer_survives_process_restart PASSED [ 85%]
test_properties.py::TestBufferedDataUpload::test_buffer_fifo_when_full PASSED [100%]

================================================================ Hypothesis Statistics =================================================================

test_properties.py::TestDataCompression::test_compressed_payload_smaller_than_original:
  - 100 passing examples, 0 failing examples, 0 invalid examples
  - Typical runtimes: ~ 0-1 ms

test_properties.py::TestDataCompression::test_batch_compression_efficiency:
  - 50 passing examples, 0 failing examples, 0 invalid examples
  - Typical runtimes: ~ 0-2 ms

test_properties.py::TestBufferedDataUpload::test_buffered_data_preserves_original_timestamps:
  - 50 passing examples, 0 failing examples, 0 invalid examples
  - Typical runtimes: ~ 50-200 ms (SQLite operations)

test_properties.py::TestBufferedDataUpload::test_buffered_data_maintains_chronological_order:
  - 30 passing examples, 0 failing examples, 0 invalid examples
  - Typical runtimes: ~ 50-200 ms (SQLite operations)

================================================================== 7 passed in 13.98s ===================================================================
```

## Benefícios dos Testes de Propriedade

1. **Cobertura Ampla:** Testa centenas de casos automaticamente ao invés de poucos casos manualmente escolhidos

2. **Detecção de Edge Cases:** Hypothesis encontra casos extremos que desenvolvedores podem não pensar

3. **Documentação Viva:** Propriedades descrevem comportamentos esperados do sistema de forma clara

4. **Regressão:** Hypothesis salva casos que falharam para re-testar em execuções futuras

5. **Confiança:** Maior confiança de que o código funciona corretamente para qualquer entrada válida

## Configuração do Hypothesis

Os testes usam as seguintes configurações:

- `max_examples=100`: Gera 100 exemplos aleatórios por teste (padrão)
- `max_examples=50`: Para testes mais lentos (batch compression)
- Estratégias de geração:
  - `st.floats()`: Gera números de ponto flutuante em ranges específicos
  - `st.integers()`: Gera inteiros em ranges específicos

## Próximas Propriedades a Implementar

Outras propriedades do sistema que podem ser testadas:

- **Property 34:** Buffer Overflow FIFO Discard (Requisito 31.6) - ✅ Implementado em test_buffer_fifo_when_full
- **Property 17:** Unauthenticated Data Submission Rejection (Requisito 8.8) - Requer backend
- **Property 7:** Valid Activation Key Registration (Requisito 3.3) - Requer backend
- **Property 8:** Removed Device Credential Revocation (Requisito 3.7) - Requer backend

## Referências

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing](https://en.wikipedia.org/wiki/Property_testing)
- [Requisitos do Sistema](../.kiro/specs/saas-multi-tenant-platform/requirements.md)
