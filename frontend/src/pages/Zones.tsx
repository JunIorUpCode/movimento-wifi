/* Zones.tsx — Tarefa 34: Gerenciamento de Zonas */

import { useEffect, useState } from 'react';
import { Plus, Pencil, Trash2, MapPin, CheckCircle, XCircle } from 'lucide-react';
import { api } from '../services/api';
import type { Zone } from '../types';

interface ZoneForm {
  name: string;
  rssi_min: number;
  rssi_max: number;
}

const EMPTY_FORM: ZoneForm = { name: '', rssi_min: -80, rssi_max: -50 };

export function Zones() {
  const [zones, setZones] = useState<Zone[]>([]);
  const [currentZone, setCurrentZone] = useState<{ current_zone: Zone | null; rssi: number | null; message: string } | null>(null);
  const [form, setForm] = useState<ZoneForm>(EMPTY_FORM);
  const [editing, setEditing] = useState<number | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [message, setMessage] = useState<{ type: 'ok' | 'err'; text: string } | null>(null);

  const loadData = async () => {
    const [z, c] = await Promise.all([api.listZones(), api.getCurrentZone()]);
    setZones(z);
    setCurrentZone(c);
  };

  useEffect(() => {
    loadData();
    const iv = setInterval(() => api.getCurrentZone().then(setCurrentZone), 5000);
    return () => clearInterval(iv);
  }, []);

  const handleSubmit = async () => {
    if (!form.name.trim()) { setMessage({ type: 'err', text: 'Nome é obrigatório.' }); return; }
    if (form.rssi_min >= form.rssi_max) { setMessage({ type: 'err', text: 'rssi_min deve ser menor que rssi_max.' }); return; }
    try {
      if (editing !== null) {
        await api.updateZone(editing, form);
        setMessage({ type: 'ok', text: 'Zona atualizada.' });
      } else {
        await api.createZone(form);
        setMessage({ type: 'ok', text: 'Zona criada.' });
      }
      setForm(EMPTY_FORM);
      setEditing(null);
      setShowForm(false);
      loadData();
    } catch (e: unknown) {
      setMessage({ type: 'err', text: e instanceof Error ? e.message : 'Erro.' });
    }
  };

  const handleEdit = (z: Zone) => {
    setForm({ name: z.name, rssi_min: z.rssi_min, rssi_max: z.rssi_max });
    setEditing(z.id);
    setShowForm(true);
    setMessage(null);
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Remover esta zona?')) return;
    try {
      await api.deleteZone(id);
      loadData();
    } catch { setMessage({ type: 'err', text: 'Erro ao remover zona.' }); }
  };

  return (
    <div className="page-content">
      <div className="page-header-row">
        <h2 className="page-title">Zonas de Monitoramento</h2>
        <button className="btn btn-primary" onClick={() => { setShowForm(true); setEditing(null); setForm(EMPTY_FORM); }}>
          <Plus size={15} /> Nova Zona
        </button>
      </div>

      {message && (
        <div className={`alert-banner ${message.type === 'ok' ? 'alert-ok' : 'alert-err'}`}>
          {message.type === 'ok' ? <CheckCircle size={16} /> : <XCircle size={16} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Zona atual */}
      {currentZone && (
        <div className="card">
          <h3 className="card-title">Zona Atual</h3>
          <div className="current-zone-row">
            <MapPin size={20} />
            <div>
              {currentZone.current_zone
                ? <><strong>{currentZone.current_zone.name}</strong> — RSSI: {currentZone.rssi?.toFixed(1)} dBm</>
                : <span className="text-muted">Nenhuma zona correspondente — RSSI: {currentZone.rssi?.toFixed(1) ?? 'N/A'} dBm</span>
              }
            </div>
          </div>
        </div>
      )}

      {/* Formulário */}
      {showForm && (
        <div className="card">
          <h3 className="card-title">{editing !== null ? 'Editar Zona' : 'Nova Zona'}</h3>
          <div className="form-row">
            <label>Nome</label>
            <input className="input" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="ex: Sala de Estar" />
          </div>
          <div className="form-row-2">
            <div className="form-row">
              <label>RSSI mín. (dBm)</label>
              <input className="input" type="number" value={form.rssi_min} onChange={(e) => setForm({ ...form, rssi_min: Number(e.target.value) })} />
            </div>
            <div className="form-row">
              <label>RSSI máx. (dBm)</label>
              <input className="input" type="number" value={form.rssi_max} onChange={(e) => setForm({ ...form, rssi_max: Number(e.target.value) })} />
            </div>
          </div>
          <div className="form-actions">
            <button className="btn btn-primary" onClick={handleSubmit}>
              {editing !== null ? 'Salvar' : 'Criar'}
            </button>
            <button className="btn btn-ghost" onClick={() => { setShowForm(false); setEditing(null); setForm(EMPTY_FORM); }}>
              Cancelar
            </button>
          </div>
        </div>
      )}

      {/* Lista de zonas */}
      <div className="card">
        <h3 className="card-title">Zonas Configuradas</h3>
        {zones.length === 0 ? (
          <p className="text-muted">Nenhuma zona configurada. Crie uma zona para associar faixas de RSSI a áreas físicas.</p>
        ) : (
          <table className="table">
            <thead>
              <tr><th>Nome</th><th>RSSI mín.</th><th>RSSI máx.</th><th>Criada em</th><th>Ações</th></tr>
            </thead>
            <tbody>
              {zones.map((z) => (
                <tr key={z.id} className={currentZone?.current_zone?.id === z.id ? 'row-active' : ''}>
                  <td>
                    {z.name}
                    {currentZone?.current_zone?.id === z.id && <span className="badge badge-green ml-sm">Atual</span>}
                  </td>
                  <td>{z.rssi_min} dBm</td>
                  <td>{z.rssi_max} dBm</td>
                  <td>{new Date(z.created_at).toLocaleDateString('pt-BR')}</td>
                  <td className="actions-cell">
                    <button className="btn btn-sm btn-ghost" onClick={() => handleEdit(z)}><Pencil size={13} /></button>
                    <button className="btn btn-sm btn-danger" onClick={() => handleDelete(z.id)}><Trash2 size={13} /></button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
