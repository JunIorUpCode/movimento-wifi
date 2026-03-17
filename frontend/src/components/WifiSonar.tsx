/* WifiSonar — Visualização tipo "sonar" do ambiente com Wi-Fi 
   
   IMPORTANTE: Esta é uma SIMULAÇÃO visual baseada em RSSI.
   Para ver formas reais de pessoas/objetos, seria necessário:
   - Hardware CSI (Intel 5300, ESP32-S3)
   - Múltiplos pontos de acesso (triangulação)
   - Algoritmos de reconstrução 3D
   - Machine Learning treinado
*/

import { useEffect, useRef, useState } from 'react';
import { useStore } from '../store/useStore';
import { EVENT_COLORS } from '../types';

interface DetectedObject {
  x: number;
  y: number;
  size: number;
  type: 'person' | 'movement' | 'unknown';
  confidence: number;
  angle: number;
}

export function WifiSonar() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const currentEvent = useStore((s) => s.currentEvent);
  const lastUpdate = useStore((s) => s.lastUpdate);
  const [scanAngle, setScanAngle] = useState(0);
  const [detectedObjects, setDetectedObjects] = useState<DetectedObject[]>([]);

  // Simula "varredura" do sonar
  useEffect(() => {
    const interval = setInterval(() => {
      setScanAngle((prev) => (prev + 2) % 360);
    }, 30); // Velocidade da varredura

    return () => clearInterval(interval);
  }, []);

  // Atualiza objetos detectados baseado nas features
  useEffect(() => {
    if (!lastUpdate) return;

    const { features, confidence, event_type } = lastUpdate;
    
    // Simula detecção de objetos baseado na energia e variância
    const objects: DetectedObject[] = [];

    if (event_type !== 'no_presence') {
      // Objeto principal (pessoa detectada)
      const energy = features.signal_energy;
      const variance = features.signal_variance;
      const instability = features.instability_score;

      // Posição simulada baseada em RSSI
      // Em um sistema real com CSI, isso seria calculado por triangulação
      const rssiNormalized = (lastUpdate.signal.rssi + 100) / 70;
      const distance = 1 - rssiNormalized; // 0 = perto, 1 = longe
      
      // Ângulo simulado (em sistema real, viria de múltiplos APs)
      const baseAngle = 45 + Math.sin(Date.now() / 5000) * 30;
      
      // Tamanho baseado na energia
      const size = 20 + energy * 3;

      objects.push({
        x: Math.cos((baseAngle * Math.PI) / 180) * distance * 150,
        y: Math.sin((baseAngle * Math.PI) / 180) * distance * 150,
        size: size,
        type: event_type === 'presence_moving' ? 'movement' : 'person',
        confidence: confidence,
        angle: baseAngle,
      });

      // Se houver alta variância, simula movimento adicional
      if (variance > 2) {
        const numMovements = Math.floor(variance);
        for (let i = 0; i < Math.min(numMovements, 3); i++) {
          const offsetAngle = baseAngle + (i - 1) * 20;
          const offsetDistance = distance * (0.8 + Math.random() * 0.4);
          
          objects.push({
            x: Math.cos((offsetAngle * Math.PI) / 180) * offsetDistance * 150,
            y: Math.sin((offsetAngle * Math.PI) / 180) * offsetDistance * 150,
            size: 10 + variance * 2,
            type: 'movement',
            confidence: confidence * 0.6,
            angle: offsetAngle,
          });
        }
      }
    }

    setDetectedObjects(objects);
  }, [lastUpdate]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    const centerX = width / 2;
    const centerY = height / 2;
    const maxRadius = Math.min(width, height) / 2 - 20;

    // Limpa canvas
    ctx.fillStyle = '#0a0c10';
    ctx.fillRect(0, 0, width, height);

    const color = EVENT_COLORS[currentEvent] || '#6b7280';

    // Desenha grid radial (tipo sonar)
    ctx.strokeStyle = '#1a1d2e';
    ctx.lineWidth = 1;

    // Círculos de distância
    for (let i = 1; i <= 4; i++) {
      const radius = (maxRadius / 4) * i;
      ctx.beginPath();
      ctx.arc(centerX, centerY, radius, 0, Math.PI * 2);
      ctx.stroke();

      // Labels de distância
      ctx.fillStyle = '#4a5568';
      ctx.font = '10px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(`${i}m`, centerX, centerY - radius + 12);
    }

    // Linhas radiais (ângulos)
    for (let i = 0; i < 12; i++) {
      const angle = (Math.PI * 2 * i) / 12;
      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(
        centerX + Math.cos(angle) * maxRadius,
        centerY + Math.sin(angle) * maxRadius
      );
      ctx.stroke();

      // Labels de ângulo
      const labelRadius = maxRadius + 15;
      const degrees = (i * 30) % 360;
      ctx.fillStyle = '#4a5568';
      ctx.font = '10px monospace';
      ctx.textAlign = 'center';
      ctx.fillText(
        `${degrees}°`,
        centerX + Math.cos(angle) * labelRadius,
        centerY + Math.sin(angle) * labelRadius + 4
      );
    }

    // Desenha linha de varredura do sonar
    const scanRad = (scanAngle * Math.PI) / 180;
    const gradient = ctx.createLinearGradient(
      centerX,
      centerY,
      centerX + Math.cos(scanRad) * maxRadius,
      centerY + Math.sin(scanRad) * maxRadius
    );
    gradient.addColorStop(0, `${color}00`);
    gradient.addColorStop(0.7, `${color}40`);
    gradient.addColorStop(1, `${color}80`);

    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.lineTo(
      centerX + Math.cos(scanRad) * maxRadius,
      centerY + Math.sin(scanRad) * maxRadius
    );
    ctx.strokeStyle = gradient;
    ctx.lineWidth = 3;
    ctx.stroke();

    // Área de varredura (cone)
    ctx.beginPath();
    ctx.moveTo(centerX, centerY);
    ctx.arc(centerX, centerY, maxRadius, scanRad - 0.3, scanRad, false);
    ctx.closePath();
    ctx.fillStyle = `${color}10`;
    ctx.fill();

    // Desenha objetos detectados
    detectedObjects.forEach((obj) => {
      const objX = centerX + obj.x;
      const objY = centerY + obj.y;

      // Só desenha se estiver na área de varredura recente
      const objAngle = Math.atan2(obj.y, obj.x) * (180 / Math.PI);
      const angleDiff = Math.abs(((objAngle - scanAngle + 180) % 360) - 180);
      
      if (angleDiff < 60) {
        const fadeAlpha = 1 - angleDiff / 60;

        // Desenha "eco" do objeto
        for (let i = 3; i > 0; i--) {
          ctx.beginPath();
          ctx.arc(objX, objY, obj.size * (i * 0.4), 0, Math.PI * 2);
          ctx.strokeStyle = `${color}${Math.floor(fadeAlpha * 30 * i).toString(16).padStart(2, '0')}`;
          ctx.lineWidth = 2;
          ctx.stroke();
        }

        // Desenha objeto principal
        ctx.beginPath();
        ctx.arc(objX, objY, obj.size, 0, Math.PI * 2);
        
        if (obj.type === 'person') {
          // Forma de pessoa (simplificada)
          ctx.fillStyle = `${color}${Math.floor(fadeAlpha * 180).toString(16).padStart(2, '0')}`;
          ctx.fill();
          
          // "Cabeça"
          ctx.beginPath();
          ctx.arc(objX, objY - obj.size * 0.6, obj.size * 0.3, 0, Math.PI * 2);
          ctx.fillStyle = `${color}${Math.floor(fadeAlpha * 220).toString(16).padStart(2, '0')}`;
          ctx.fill();
        } else {
          // Movimento (forma irregular)
          ctx.fillStyle = `${color}${Math.floor(fadeAlpha * 120).toString(16).padStart(2, '0')}`;
          ctx.fill();
        }

        // Label de confiança
        ctx.fillStyle = `${color}${Math.floor(fadeAlpha * 255).toString(16).padStart(2, '0')}`;
        ctx.font = '10px monospace';
        ctx.textAlign = 'center';
        ctx.fillText(
          `${Math.floor(obj.confidence * 100)}%`,
          objX,
          objY + obj.size + 15
        );

        // Linha de conexão ao centro
        ctx.beginPath();
        ctx.moveTo(centerX, centerY);
        ctx.lineTo(objX, objY);
        ctx.strokeStyle = `${color}${Math.floor(fadeAlpha * 40).toString(16).padStart(2, '0')}`;
        ctx.lineWidth = 1;
        ctx.setLineDash([5, 5]);
        ctx.stroke();
        ctx.setLineDash([]);
      }
    });

    // Desenha centro (transmissor)
    ctx.beginPath();
    ctx.arc(centerX, centerY, 8, 0, Math.PI * 2);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.strokeStyle = `${color}80`;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Pulso do transmissor
    const pulseRadius = 8 + Math.sin(Date.now() / 200) * 4;
    ctx.beginPath();
    ctx.arc(centerX, centerY, pulseRadius, 0, Math.PI * 2);
    ctx.strokeStyle = `${color}40`;
    ctx.lineWidth = 2;
    ctx.stroke();

    // Info no canto
    ctx.fillStyle = '#9ca3af';
    ctx.font = '11px monospace';
    ctx.textAlign = 'left';
    ctx.fillText(`SCAN: ${scanAngle.toFixed(0)}°`, 10, 20);
    ctx.fillText(`OBJETOS: ${detectedObjects.length}`, 10, 35);
    
    if (lastUpdate) {
      ctx.fillText(`RSSI: ${lastUpdate.signal.rssi.toFixed(1)} dBm`, 10, 50);
    }

  }, [scanAngle, detectedObjects, currentEvent, lastUpdate]);

  return (
    <div className="wifi-sonar-container">
      <div className="wifi-sonar-header">
        <h3 className="chart-title">Sonar Wi-Fi (Simulação)</h3>
        <div className="sonar-warning">
          ⚠️ Visualização simulada - Requer CSI para formas reais
        </div>
      </div>
      <div className="wifi-sonar-wrapper">
        <canvas
          ref={canvasRef}
          width={500}
          height={500}
          className="wifi-sonar-canvas"
        />
      </div>
      <div className="wifi-sonar-info">
        <div className="info-item">
          <span className="info-label">Modo:</span>
          <span className="info-value">RSSI (Limitado)</span>
        </div>
        <div className="info-item">
          <span className="info-label">Precisão:</span>
          <span className="info-value">Baixa (sem CSI)</span>
        </div>
        <div className="info-item">
          <span className="info-label">Objetos:</span>
          <span className="info-value">{detectedObjects.length}</span>
        </div>
      </div>
      <div className="wifi-sonar-note">
        <strong>Nota:</strong> Esta é uma simulação visual. Para ver formas reais de pessoas/objetos,
        seria necessário hardware CSI (Intel 5300, ESP32-S3) e múltiplos pontos de acesso.
        Veja <code>SONAR_WIFI_REAL.md</code> para mais informações.
      </div>
    </div>
  );
}
