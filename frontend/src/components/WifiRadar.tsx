/* WifiRadar — Visualização de movimento detectado por ondas Wi-Fi */

import { useEffect, useRef } from 'react';
import { useStore } from '../store/useStore';
import { EVENT_COLORS } from '../types';

export function WifiRadar() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const currentEvent = useStore((s) => s.currentEvent);
  const lastUpdate = useStore((s) => s.lastUpdate);
  const signalHistory = useStore((s) => s.signalHistory);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Configuração do canvas
    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;

    // Limpa canvas
    ctx.fillStyle = '#0f1117';
    ctx.fillRect(0, 0, width, height);

    // Cor baseada no evento atual
    const color = EVENT_COLORS[currentEvent] || '#6b7280';

    // Desenha círculos concêntricos (ondas Wi-Fi)
    const numCircles = 5;
    for (let i = numCircles; i > 0; i--) {
      const radius = (Math.min(width, height) / 2) * (i / numCircles) * 0.85;
      const alpha = 0.1 + (i / numCircles) * 0.1;
      
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.strokeStyle = `${color}${Math.floor(alpha * 255).toString(16).padStart(2, '0')}`;
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Desenha linhas radiais
    const numLines = 12;
    for (let i = 0; i < numLines; i++) {
      const angle = (Math.PI * 2 * i) / numLines;
      const x = centerX + Math.cos(angle) * (Math.min(width, height) / 2) * 0.85;
      const y = centerY + Math.sin(angle) * (Math.min(width, height) / 2) * 0.85;
      
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(x, y);
      ctx.strokeStyle = `${color}15`;
      ctx.lineWidth = 1;
      ctx.stroke();
    }

    // Calcula intensidade baseada nas features
    let intensity = 0;
    let spread = 0;

    if (lastUpdate) {
      // Intensidade baseada na energia do sinal
      intensity = Math.min(lastUpdate.features.signal_energy / 20, 1);
      
      // Dispersão baseada na variância
      spread = Math.min(lastUpdate.features.signal_variance / 5, 1);
    }

    // Desenha "blob" central representando movimento
    const baseRadius = 30;
    const maxRadius = Math.min(width, height) / 2 * 0.7;
    const blobRadius = baseRadius + (maxRadius - baseRadius) * intensity;

    // Efeito de "pulso" para movimento
    const pulseIntensity = currentEvent === 'presence_moving' ? 0.3 : 0.1;
    const pulse = Math.sin(Date.now() / 500) * pulseIntensity;

    // Desenha blob com gradiente
    const gradient = ctx.createRadialGradient(
      centerX, centerY, 0,
      centerX, centerY, blobRadius * (1 + pulse)
    );
    
    const mainAlpha = 0.3 + intensity * 0.4;
    gradient.addColorStop(0, `${color}${Math.floor(mainAlpha * 255).toString(16).padStart(2, '0')}`);
    gradient.addColorStop(0.5, `${color}${Math.floor(mainAlpha * 0.5 * 255).toString(16).padStart(2, '0')}`);
    gradient.addColorStop(1, `${color}00`);

    ctx.beginPath();
    ctx.arc(centerX, centerY, blobRadius * (1 + pulse), 0, Math.PI * 2);
    ctx.fillStyle = gradient;
    ctx.fill();

    // Desenha "ondas" de movimento se houver movimento ativo
    if (currentEvent === 'presence_moving' || currentEvent === 'fall_suspected') {
      const time = Date.now() / 1000;
      const numWaves = 3;
      
      for (let i = 0; i < numWaves; i++) {
        const wavePhase = (time * 2 + i * 0.5) % 2;
        const waveRadius = blobRadius + wavePhase * 80;
        const waveAlpha = (1 - wavePhase / 2) * 0.3;
        
        ctx.beginPath();
        ctx.arc(centerX, centerY, waveRadius, 0, Math.PI * 2);
        ctx.strokeStyle = `${color}${Math.floor(waveAlpha * 255).toString(16).padStart(2, '0')}`;
        ctx.lineWidth = 3;
        ctx.stroke();
      }
    }

    // Desenha partículas para representar dispersão
    if (spread > 0.2) {
      const numParticles = Math.floor(spread * 20);
      const particleRadius = blobRadius * 1.5;
      
      for (let i = 0; i < numParticles; i++) {
        const angle = (Math.PI * 2 * i) / numParticles + Date.now() / 2000;
        const distance = particleRadius + Math.sin(Date.now() / 1000 + i) * 20;
        const x = centerX + Math.cos(angle) * distance;
        const y = centerY + Math.sin(angle) * distance;
        const size = 2 + Math.random() * 2;
        
        ctx.beginPath();
        ctx.arc(x, y, size, 0, Math.PI * 2);
        ctx.fillStyle = `${color}${Math.floor(spread * 128).toString(16).padStart(2, '0')}`;
        ctx.fill();
      }
    }

    // Desenha indicador de RSSI no canto
    if (lastUpdate) {
      const rssi = lastUpdate.signal.rssi;
      const rssiNormalized = Math.max(0, Math.min(1, (rssi + 100) / 70)); // -100 a -30 dBm
      
      // Barra de RSSI
      const barWidth = 8;
      const barHeight = 60;
      const barX = width - 30;
      const barY = 20;
      
      // Fundo da barra
      ctx.fillStyle = '#2a2d3a';
      ctx.fillRect(barX, barY, barWidth, barHeight);
      
      // Preenchimento da barra
      const fillHeight = barHeight * rssiNormalized;
      ctx.fillStyle = color;
      ctx.fillRect(barX, barY + barHeight - fillHeight, barWidth, fillHeight);
      
      // Texto RSSI
      ctx.fillStyle = '#9ca3af';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'right';
      ctx.fillText(`${rssi.toFixed(0)}`, barX - 5, barY + barHeight / 2 + 4);
      ctx.fillText('dBm', barX - 5, barY + barHeight / 2 + 16);
    }

    // Texto central com estado
    ctx.fillStyle = color;
    ctx.font = 'bold 14px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText(
      currentEvent === 'no_presence' ? 'SEM PRESENÇA' :
      currentEvent === 'presence_still' ? 'PARADO' :
      currentEvent === 'presence_moving' ? 'MOVIMENTO' :
      currentEvent === 'fall_suspected' ? 'QUEDA!' :
      'INATIVO',
      centerX,
      height - 20
    );

  }, [currentEvent, lastUpdate, signalHistory]);

  // Anima o canvas
  useEffect(() => {
    const interval = setInterval(() => {
      // Força re-render para animação
      canvasRef.current?.getContext('2d');
    }, 50); // 20 FPS

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="wifi-radar-container">
      <h3 className="chart-title">Visualização de Movimento (Wi-Fi)</h3>
      <div className="wifi-radar-wrapper">
        <canvas
          ref={canvasRef}
          width={400}
          height={400}
          className="wifi-radar-canvas"
        />
      </div>
      <div className="wifi-radar-legend">
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#6b7280' }} />
          <span>Sem presença</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#3b82f6' }} />
          <span>Parado</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#10b981' }} />
          <span>Movimento</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot" style={{ backgroundColor: '#ef4444' }} />
          <span>Queda</span>
        </div>
      </div>
    </div>
  );
}
