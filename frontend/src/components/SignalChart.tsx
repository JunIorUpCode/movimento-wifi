/* SignalChart — Gráfico em tempo real com Recharts */

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { useStore } from '../store/useStore';

export function SignalChart() {
  const signalHistory = useStore((s) => s.signalHistory);

  return (
    <div className="chart-container">
      <h3 className="chart-title">Sinal em Tempo Real</h3>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={signalHistory}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2a2d3a" />
          <XAxis
            dataKey="time"
            stroke="#6b7280"
            tick={{ fontSize: 11 }}
            interval="preserveStartEnd"
          />
          <YAxis stroke="#6b7280" tick={{ fontSize: 11 }} />
          <Tooltip
            contentStyle={{
              backgroundColor: '#1e2030',
              border: '1px solid #2a2d3a',
              borderRadius: '8px',
              color: '#e4e4e7',
            }}
          />
          <Legend />
          <Line
            type="monotone"
            dataKey="rssi"
            stroke="#3b82f6"
            name="RSSI (dBm)"
            strokeWidth={2}
            dot={false}
            animationDuration={200}
          />
          <Line
            type="monotone"
            dataKey="energy"
            stroke="#10b981"
            name="Energia"
            strokeWidth={2}
            dot={false}
            animationDuration={200}
          />
          <Line
            type="monotone"
            dataKey="variance"
            stroke="#f59e0b"
            name="Variância"
            strokeWidth={2}
            dot={false}
            animationDuration={200}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
