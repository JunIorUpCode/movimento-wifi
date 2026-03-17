"""
Script para monitorar valores em tempo real e ajudar a calibrar detecção de queda.
"""

import asyncio
import httpx
import time


async def monitorar_valores():
    """Monitora valores do sinal em tempo real."""
    
    print("="*70)
    print("MONITORAMENTO DE VALORES EM TEMPO REAL")
    print("="*70)
    print("\nPara detectar queda, precisamos:")
    print("  • Taxa de mudança (rate_of_change) > 8.0 dB/s")
    print("  • OU Energia (signal_energy) > 20.0")
    print("\nFaça movimentos e veja os valores:")
    print("="*70)
    print()
    
    max_rate = 0.0
    max_energy = 0.0
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            while True:
                try:
                    response = await client.get("http://localhost:8000/api/status")
                    
                    if response.status_code == 200:
                        status = response.json()
                        features = status.get('features')
                        
                        if features:
                            rate = features.get('rate_of_change', 0)
                            energy = features.get('signal_energy', 0)
                            variance = features.get('signal_variance', 0)
                            event = status.get('current_event', 'unknown')
                            
                            # Atualiza máximos
                            if rate > max_rate:
                                max_rate = rate
                            if energy > max_energy:
                                max_energy = energy
                            
                            # Limpa linha
                            print("\r" + " "*100, end="")
                            
                            # Mostra valores
                            rate_status = "🔴 QUEDA!" if rate >= 8.0 else "🟢"
                            energy_status = "🔴 QUEDA!" if energy >= 20.0 else "🟢"
                            
                            print(
                                f"\r{rate_status} Taxa: {rate:6.2f} dB/s (max: {max_rate:6.2f}) | "
                                f"{energy_status} Energia: {energy:6.2f} (max: {max_energy:6.2f}) | "
                                f"Var: {variance:5.2f} | {event}",
                                end="",
                                flush=True
                            )
                    
                    await asyncio.sleep(0.5)
                    
                except httpx.RequestError:
                    print("\r❌ Erro ao conectar ao backend", end="", flush=True)
                    await asyncio.sleep(1)
                    
    except KeyboardInterrupt:
        print("\n\n" + "="*70)
        print("RESUMO")
        print("="*70)
        print(f"\nMáxima taxa de mudança detectada: {max_rate:.2f} dB/s")
        print(f"Máxima energia detectada: {max_energy:.2f}")
        print()
        
        if max_rate < 8.0 and max_energy < 20.0:
            print("⚠️  PROBLEMA: Valores não atingiram limiares de queda!")
            print()
            print("Soluções:")
            print("1. Faça movimentos MAIS BRUSCOS")
            print("2. Fique MAIS PRÓXIMO do roteador")
            print("3. Ou reduza os limiares:")
            print(f"   - Taxa: 8.0 → {max_rate * 0.8:.1f} dB/s")
            print(f"   - Energia: 20.0 → {max_energy * 0.8:.1f}")
        else:
            print("✅ Valores atingiram limiares! Queda deveria ser detectada.")
            print()
            print("Se não recebeu alerta, verifique:")
            print("1. Telegram está configurado?")
            print("2. Cooldown expirou? (30s entre alertas)")
            print("3. Confiança mínima está em 60%?")
        
        print()


if __name__ == "__main__":
    asyncio.run(monitorar_valores())
