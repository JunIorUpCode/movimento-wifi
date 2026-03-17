# Property 13: BÁSICO Plan CSI Data Rejection

## Resumo da Implementação

Implementado teste de propriedade e funcionalidade para validar que dispositivos com plano BÁSICO não podem enviar dados CSI.

## Requisitos Validados

- **Requisito 5.2**: "WHEN a device with BÁSICO plan attempts CSI capture, THE Backend_Central SHALL reject the data"

## Implementação

### 1. Endpoint de Recepção de Dados

**Arquivo**: `services/device-service/routes/device.py`

Criado novo endpoint `POST /api/devices/{device_id}/data` que:
- Recebe dados de sinal do dispositivo (RSSI ou CSI)
- Valida o JWT token do dispositivo
- Verifica o plan_type no token
- Rejeita dados CSI de dispositivos BÁSICO com HTTP 403
- Aceita dados RSSI de dispositivos BÁSICO
- Aceita qualquer tipo de dados de dispositivos PREMIUM

### 2. JWT Token com Plan Type

**Arquivo**: `services/device-service/services/device_registration.py`

Atualizado método `generate_device_jwt()` para incluir `plan_type` no payload:
- Adiciona campo `plan_type` ao JWT
- Permite validação do plano sem consultar banco de dados
- Mantém consistência com o plano da licença

### 3. Teste de Propriedade

**Arquivo**: `services/device-service/test_device_service.py`

Implementado `test_property_basic_plan_csi_data_rejection()` que valida:

#### Cenário de Teste

1. **Registro**: Dispositivo é registrado com plano BÁSICO
2. **Validação do Token**: JWT contém plan_type="basic"
3. **Tentativa CSI**: Dispositivo tenta enviar dados CSI
4. **Rejeição**: Sistema rejeita com HTTP 403
5. **Mensagem**: Erro sugere upgrade para PREMIUM
6. **Validação RSSI**: Dispositivo BÁSICO pode enviar RSSI

#### Validações da Propriedade

- ✅ Submissão de CSI é rejeitada (success=False)
- ✅ Status code é HTTP 403 Forbidden
- ✅ Mensagem menciona plano BÁSICO
- ✅ Mensagem sugere upgrade para PREMIUM
- ✅ Mensagem menciona CSI
- ✅ Dados RSSI são aceitos (status 200)

## Execução dos Testes

```bash
# Executar apenas este teste
python -m pytest services/device-service/test_device_service.py::TestPropertyBasedDeviceRegistration::test_property_basic_plan_csi_data_rejection -v

# Executar todos os testes de propriedade
python -m pytest services/device-service/test_device_service.py::TestPropertyBasedDeviceRegistration -v
```

## Resultados

✅ **Teste passou com 50 exemplos gerados pelo Hypothesis**
✅ **Todos os 4 testes de propriedade passaram**
✅ **Nenhuma regressão detectada**

## Arquivos Modificados

1. `services/device-service/routes/device.py`
   - Adicionado schema `DeviceDataRequest`
   - Adicionado endpoint `POST /api/devices/{device_id}/data`
   - Implementada validação de plan_type vs data_type

2. `services/device-service/services/device_registration.py`
   - Atualizado `generate_device_jwt()` para incluir plan_type
   - Atualizada chamada do método com plan_type

3. `services/device-service/test_device_service.py`
   - Adicionado `test_property_basic_plan_csi_data_rejection()`
   - Validação completa com Hypothesis (50 exemplos)

## Próximos Passos

- [ ] Implementar event-service para processar dados recebidos
- [ ] Adicionar métricas de rejeição de dados CSI
- [ ] Implementar logs de auditoria para tentativas de envio CSI em plano BÁSICO
