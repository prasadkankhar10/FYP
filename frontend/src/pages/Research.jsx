import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, Save, Download, Loader2, RefreshCw, Box, Layers, BrainCircuit } from 'lucide-react';
import api from '../api';

const Research = () => {
  const [config, setConfig] = useState({
    alpha: 0.5,
    beta: 0.3,
    gamma: 0.2,
    propagation_factor_fail: 0.15,
    propagation_factor_pass: 0.05
  });
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    fetchConfig();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await api.get('/graph/config');
      setConfig(res.data);
    } catch (err) {
      console.error("Failed to fetch graph config:", err);
      window.dispatchEvent(new CustomEvent('show-toast', { detail: { message: "Failed to load config", type: "error" }}));
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setSaving(true);
    try {
      await api.put('/graph/config', config);
      window.dispatchEvent(new CustomEvent('show-toast', { detail: { message: "Algorithm parameters updated and edges recalculated.", type: "success" }}));
    } catch (err) {
      console.error("Failed to update config:", err);
      window.dispatchEvent(new CustomEvent('show-toast', { detail: { message: "Failed to save configuration.", type: "error" }}));
    } finally {
      setSaving(false);
    }
  };

  const handleExportDataset = async () => {
    setExporting(true);
    try {
      const res = await api.get('/analytics/export-dataset');
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `neural-audit-dataset-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.dispatchEvent(new CustomEvent('show-toast', { detail: { message: "Dataset exported successfully.", type: "success" }}));
    } catch (err) {
      console.error("Failed to export dataset:", err);
      window.dispatchEvent(new CustomEvent('show-toast', { detail: { message: "Failed to export dataset.", type: "error" }}));
    } finally {
      setExporting(false);
    }
  };

  const SliderField = ({ label, description, value, onChange, min = 0, max = 1, step = 0.01 }) => (
    <div className="mb-6">
      <div className="flex justify-between items-end mb-2">
        <div>
          <label className="text-sm font-bold text-white block">{label}</label>
          <span className="text-xs text-slate-400">{description}</span>
        </div>
        <span className="text-primary font-black bg-primary/10 px-3 py-1 rounded-lg border border-primary/20">
          {value.toFixed(2)}
        </span>
      </div>
      <input 
        type="range" 
        min={min} max={max} step={step} 
        value={value} 
        onChange={(e) => onChange(parseFloat(e.target.value))}
        className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-primary"
      />
    </div>
  );

  if (loading) {
    return (
      <div className="flex h-[80vh] items-center justify-center">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  // Calculate sum of a, b, c to show if it equals 1.0
  const weightSum = config.alpha + config.beta + config.gamma;
  const isNormalized = Math.abs(weightSum - 1.0) < 0.01;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 md:p-8 max-w-5xl w-full mx-auto"
    >
      <header className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-2 text-white flex items-center gap-4">
            <Box className="text-primary" size={48} /> Research Labs
          </h1>
          <p className="text-slate-500 font-medium max-w-2xl">
            Fine-tune the neural propagation algorithms and export your data for external scientific benchmarking.
          </p>
        </div>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Col: Algorithm Config */}
        <div className="lg:col-span-2 space-y-6">
          <div className="glass-card p-8 rounded-[2rem] border border-white/5 relative overflow-hidden">
            <h2 className="text-2xl font-black text-white mb-6 flex items-center gap-3">
              <BrainCircuit className="text-primary" /> Graph Edge Weights
            </h2>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed">
              Adjust how the Knowledge Graph calculates the final synaptic weight between concepts. 
              Ideally, Alpha + Beta + Gamma should equal 1.0. 
              <br/>Current Sum: <strong className={isNormalized ? 'text-success' : 'text-warning'}>{weightSum.toFixed(2)}</strong>
            </p>

            <SliderField 
              label="Alpha (α) — Expert Weight" 
              description="Weight derived from the parent-child hierarchy."
              value={config.alpha}
              onChange={(v) => setConfig({...config, alpha: v})}
            />
            <SliderField 
              label="Beta (β) — Data Weight" 
              description="Weight derived from co-review and co-failure correlation."
              value={config.beta}
              onChange={(v) => setConfig({...config, beta: v})}
            />
            <SliderField 
              label="Gamma (γ) — Semantic Weight" 
              description="Weight derived from text embedding similarity."
              value={config.gamma}
              onChange={(v) => setConfig({...config, gamma: v})}
            />
          </div>

          <div className="glass-card p-8 rounded-[2rem] border border-white/5 relative overflow-hidden">
            <h2 className="text-2xl font-black text-white mb-6 flex items-center gap-3">
              <Layers className="text-accent" /> Stability Propagation
            </h2>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed">
              Control how much memory stability (ΔS) cascades to neighboring concepts during a review.
            </p>

            <SliderField 
              label="Failure Propagation Factor" 
              description="Multiplier applied when you FAIL a concept (Rating = Again)."
              value={config.propagation_factor_fail}
              max={0.5}
              onChange={(v) => setConfig({...config, propagation_factor_fail: v})}
            />
            <SliderField 
              label="Success Propagation Factor" 
              description="Multiplier applied when you PASS a concept (Rating = Good/Easy)."
              value={config.propagation_factor_pass}
              max={0.5}
              onChange={(v) => setConfig({...config, propagation_factor_pass: v})}
            />
          </div>
          
          <button 
            onClick={handleSaveConfig}
            disabled={saving}
            className="w-full bg-primary hover:bg-primary/80 text-white font-black uppercase tracking-widest text-sm py-5 rounded-2xl flex justify-center items-center gap-3 transition-all shadow-xl shadow-primary/20 disabled:opacity-50"
          >
            {saving ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
            Commit Parameters & Recalculate Graph
          </button>
        </div>

        {/* Right Col: Dataset Export */}
        <div className="space-y-6">
          <div className="glass-card p-8 rounded-[2rem] border border-white/5 h-full flex flex-col items-center justify-center text-center">
            <div className="w-20 h-20 bg-success/10 rounded-full flex items-center justify-center mb-6">
              <Download className="text-success" size={36} />
            </div>
            <h3 className="text-2xl font-black text-white mb-4">Export Dataset</h3>
            <p className="text-sm text-slate-400 mb-8 leading-relaxed">
              Download your complete review history, graph state, and propagation events as a JSON dataset. 
              Perfect for offline benchmarking SM-2 vs FSRS vs Multi-FSRS.
            </p>
            <button 
              onClick={handleExportDataset}
              disabled={exporting}
              className="w-full glass bg-white/5 hover:bg-white/10 text-white font-bold uppercase tracking-widest text-xs py-4 rounded-xl flex justify-center items-center gap-2 border border-white/10 transition-all disabled:opacity-50"
            >
              {exporting ? <Loader2 className="animate-spin" size={18} /> : <RefreshCw size={18} />}
              Generate Benchmark JSON
            </button>
          </div>
        </div>

      </div>
    </motion.div>
  );
};

export default Research;
