import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Loader2, Box, Layers, Zap, RotateCcw, Maximize2, Info, LayoutGrid, 
  Terminal, Settings, Settings2, Cpu, Sparkles, Check, AlertCircle, 
  AlertTriangle, GitBranch, ArrowRight, BookOpen, Code2, HelpCircle, 
  X, Network, ExternalLink, Activity, ArrowUpRight, ChevronRight, FileText,
  Eye, EyeOff, Copy
} from 'lucide-react';
import ForceGraph2D from 'react-force-graph-2d';
import api from '../api';

const KnowledgeGraph = () => {
  const navigate = useNavigate();
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [devMode, setDevMode] = useState(false);
  const [highlightedSubject, setHighlightedSubject] = useState(null);
  const [showSettings, setShowSettings] = useState(false);
  const [lockGraph, setLockGraph] = useState(window.innerWidth < 768);
  const [tuningStatus, setTuningStatus] = useState({ loading: false, message: '', type: '' });
  const [bridges, setBridges] = useState(null);
  const [activeDetailTab, setActiveDetailTab] = useState('card'); // 'card' | 'synapses' | 'stats'
  const [showSolution, setShowSolution] = useState(true);
  const [copiedCode, setCopiedCode] = useState(false);
  const fgRef = useRef();

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const res = await api.get('/graph/full');
        setGraphData(res.data);
      } catch (err) {
        console.error('Failed to load graph', err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, []);

  const handleTuneWeights = async () => {
    setTuningStatus({ loading: true, message: 'Re-calculating synaptic influence...', type: 'info' });
    try {
      await api.post('/graph/tune-weights');
      setTuningStatus({ loading: false, message: 'Neural weights balanced successfully!', type: 'success' });
      const gRes = await api.get('/graph/full');
      setGraphData(gRes.data);
    } catch (err) {
      setTuningStatus({ loading: false, message: 'Weight tuning failed.', type: 'error' });
    }
  };

  const handleOptimizeFsrs = async () => {
    setTuningStatus({ loading: true, message: 'Crunching memory logs for optimization...', type: 'info' });
    try {
      const res = await api.post('/analytics/optimize-fsrs');
      if (res.data.success === false) {
        setTuningStatus({ loading: false, message: res.data.message, type: 'error' });
      } else {
        setTuningStatus({ loading: false, message: 'FSRS parameters optimized!', type: 'success' });
      }
    } catch (err) {
      setTuningStatus({ loading: false, message: 'Optimization engine error.', type: 'error' });
    }
  };

  const handleSuggestBridges = async () => {
    setTuningStatus({ loading: true, message: 'AI identifying island concepts...', type: 'info' });
    try {
      const res = await api.post('/ai/suggest-bridges');
      setBridges(res.data.bridges);
      setTuningStatus({ loading: false, message: 'Neural bridges suggested!', type: 'success' });
    } catch (err) {
      setTuningStatus({ loading: false, message: 'Bridge identification failed.', type: 'error' });
    }
  };

  const handleConnectAll = async () => {
    setTuningStatus({ loading: true, message: 'Synthesizing neural connections across all concepts...', type: 'info' });
    try {
      const res = await api.post('/graph/connect-all');
      setTuningStatus({ 
        loading: false, 
        message: res.data.message || `Connected all concepts into neural network!`, 
        type: 'success' 
      });
      const gRes = await api.get('/graph/full');
      setGraphData(gRes.data);
      if (fgRef.current) {
        fgRef.current.d3ReheatSimulation();
      }
    } catch (err) {
      setTuningStatus({ loading: false, message: 'Failed to connect concepts.', type: 'error' });
    }
  };

  const data = useMemo(() => {
    if (!graphData) return { nodes: [], links: [] };
    return {
      nodes: graphData.nodes.map(n => {
        const isCS = ['code', 'programming', 'ds', 'algo', 'oop'].some(k => n.title.toLowerCase().includes(k) || (n.subject_name || '').toLowerCase().includes(k));
        return {
          id: n.concept_id,
          name: n.title,
          val: 8 + (n.neighbor_count * 2),
          color: n.retrievability >= 0.85 ? '#10b981' : n.retrievability >= 0.5 ? '#f59e0b' : '#f43f5e',
          isCS,
          ...n
        };
      }),
      links: graphData.edges.map(e => ({
        source: e.source_concept_id,
        target: e.target_concept_id,
        value: e.w_final,
        ...e
      }))
    };
  }, [graphData, devMode]);

  // Find all connected concepts for the selected node
  const relatedConcepts = useMemo(() => {
    if (!selectedNode || !graphData?.nodes || !graphData?.edges) return [];
    const currentId = selectedNode.concept_id || selectedNode.id;
    const neighborMap = new Map();

    graphData.edges.forEach(e => {
      if (e.source_concept_id === currentId) {
        const targetNode = graphData.nodes.find(n => n.concept_id === e.target_concept_id);
        if (targetNode) {
          neighborMap.set(targetNode.concept_id, {
            ...targetNode,
            id: targetNode.concept_id,
            name: targetNode.title,
            val: 8 + (targetNode.neighbor_count * 2),
            color: targetNode.retrievability >= 0.85 ? '#10b981' : targetNode.retrievability >= 0.5 ? '#f59e0b' : '#f43f5e',
            weight: e.w_final,
            expertWeight: e.w_expert,
            semanticWeight: e.w_semantic,
            direction: 'Outgoing Synapse'
          });
        }
      } else if (e.target_concept_id === currentId) {
        const sourceNode = graphData.nodes.find(n => n.concept_id === e.source_concept_id);
        if (sourceNode && !neighborMap.has(sourceNode.concept_id)) {
          neighborMap.set(sourceNode.concept_id, {
            ...sourceNode,
            id: sourceNode.concept_id,
            name: sourceNode.title,
            val: 8 + (sourceNode.neighbor_count * 2),
            color: sourceNode.retrievability >= 0.85 ? '#10b981' : sourceNode.retrievability >= 0.5 ? '#f59e0b' : '#f43f5e',
            weight: e.w_final,
            expertWeight: e.w_expert,
            semanticWeight: e.w_semantic,
            direction: 'Incoming Synapse'
          });
        }
      }
    });
    return Array.from(neighborMap.values()).sort((a, b) => (b.weight || 0) - (a.weight || 0));
  }, [selectedNode, graphData]);

  // Set of neighbor IDs for canvas highlight
  const neighborIds = useMemo(() => {
    if (!selectedNode) return new Set();
    const currentId = selectedNode.concept_id || selectedNode.id;
    const s = new Set();
    graphData?.edges?.forEach(e => {
      if (e.source_concept_id === currentId) s.add(e.target_concept_id);
      if (e.target_concept_id === currentId) s.add(e.source_concept_id);
    });
    return s;
  }, [selectedNode, graphData]);

  // Parse front/back or raw text content of selected node
  const parsedContent = useMemo(() => {
    if (!selectedNode?.content) return null;
    try {
      const trimmed = selectedNode.content.trim();
      if (trimmed.startsWith('{') && trimmed.endsWith('}')) {
        const json = JSON.parse(trimmed);
        if (json.front || json.back) {
          return json;
        }
      }
    } catch (e) {}
    return { raw: selectedNode.content };
  }, [selectedNode]);

  const resetView = useCallback(() => {
    if (fgRef.current) {
      fgRef.current.zoomToFit(800, 100);
      setSelectedNode(null);
    }
  }, []);

  const subjects = useMemo(() => {
    if (!graphData) return [];
    const subMap = {};
    graphData.nodes.forEach(n => {
      const sId = n.subject_id || 0;
      if (!subMap[sId]) {
        subMap[sId] = { id: sId, name: n.subject_name || 'Uncategorized', count: 0 };
      }
      subMap[sId].count++;
    });
    return Object.values(subMap);
  }, [graphData]);

  const zoomToSubject = (subjectId) => {
    if (!fgRef.current || !graphData) return;
    
    if (highlightedSubject === subjectId) {
      setHighlightedSubject(null);
      fgRef.current.zoomToFit(800, 100);
    } else {
      setHighlightedSubject(subjectId);
      fgRef.current.zoomToFit(800, 100, node => node.subject_id === subjectId);
      setSelectedNode(null);
    }
  };

  useEffect(() => {
    if (!fgRef.current || loading || !graphData) return;

    const subjectsList = [...new Set(graphData.nodes.map(n => n.subject_id))];
    const subjectCenters = {};
    const clusterRadius = Math.max(250, graphData.nodes.length * 8);
    
    subjectsList.forEach((sid, i) => {
      const angle = (i / subjectsList.length) * 2 * Math.PI;
      subjectCenters[sid] = {
        x: Math.cos(angle) * clusterRadius,
        y: Math.sin(angle) * clusterRadius
      };
    });

    fgRef.current.d3Force('charge').strength(-250).distanceMax(500);
    fgRef.current.d3Force('link').distance(60);
    
    fgRef.current.d3Force('subject', (alpha) => {
      data.nodes.forEach(node => {
        const center = subjectCenters[node.subject_id];
        if (center) {
          node.vx += (center.x - node.x) * alpha * 0.15;
          node.vy += (center.y - node.y) * alpha * 0.15;
        }
      });
    });

    const timer = setTimeout(resetView, 1200);
    return () => clearTimeout(timer);
  }, [loading, graphData, data, resetView]);

  const handleNodeClick = (node) => {
    if (fgRef.current) {
      fgRef.current.centerAt(node.x, node.y, 1000);
      fgRef.current.zoom(2, 1000);
    }
    setSelectedNode(node);
    setActiveDetailTab('card');
    setShowSolution(true);
  };

  const handleCopyCode = (codeText) => {
    if (!codeText) return;
    navigator.clipboard.writeText(codeText);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  const drawNode = useCallback((node, ctx, globalScale) => {
    if (!isFinite(node.x) || !isFinite(node.y)) return;
    const r = Math.sqrt(node.val) * 2.5;
    const nodeId = node.concept_id || node.id;
    const selId = selectedNode?.concept_id || selectedNode?.id;
    const isSelected = selId === nodeId;
    const isNeighbor = neighborIds.has(nodeId);

    let opacity = 1;
    if (selId) {
      opacity = isSelected ? 1 : isNeighbor ? 1 : 0.15;
    } else if (highlightedSubject) {
      opacity = node.subject_id === highlightedSubject ? 1 : 0.1;
    }

    if (devMode && node.isCS) {
       ctx.fillStyle = opacity < 1 ? 'rgba(255,255,255,0.05)' : node.color;
       ctx.shadowBlur = opacity < 1 ? 0 : 15;
       ctx.shadowColor = node.color;
       ctx.fillRect(node.x - r, node.y - r, r * 2, r * 2);
       ctx.shadowBlur = 0;
    } else {
       const gradient = ctx.createRadialGradient(node.x, node.y, r, node.x, node.y, r * 2.5);
       gradient.addColorStop(0, (opacity < 1 ? 'rgba(255,255,255,0.02)' : node.color + (isSelected ? '80' : '40')));
       gradient.addColorStop(1, 'transparent');
       ctx.fillStyle = gradient;
       ctx.beginPath();
       ctx.arc(node.x, node.y, r * (isSelected ? 3.5 : 2.5), 0, 2 * Math.PI, false);
       ctx.fill();

       ctx.fillStyle = opacity < 1 ? 'rgba(255,255,255,0.1)' : node.color;
       ctx.beginPath();
       ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
       ctx.fill();
    }

    if (isSelected) {
       ctx.strokeStyle = '#ffffff';
       ctx.lineWidth = 3 / globalScale;
       ctx.beginPath();
       ctx.arc(node.x, node.y, r + 4 / globalScale, 0, 2 * Math.PI, false);
       ctx.stroke();

       ctx.strokeStyle = '#8b5cf6';
       ctx.lineWidth = 1.5 / globalScale;
       ctx.beginPath();
       ctx.arc(node.x, node.y, r + 7 / globalScale, 0, 2 * Math.PI, false);
       ctx.stroke();
    } else if (isNeighbor) {
       ctx.strokeStyle = '#c084fc';
       ctx.lineWidth = 2 / globalScale;
       ctx.beginPath();
       ctx.arc(node.x, node.y, r + 3 / globalScale, 0, 2 * Math.PI, false);
       ctx.stroke();
    }

    if ((globalScale > 0.7 && opacity >= 0.8) || isSelected || isNeighbor) {
      const label = node.name || node.title;
      const fontSize = (isSelected ? 16 : isNeighbor ? 13 : 11) / globalScale;
      ctx.font = `bold ${fontSize}px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      const textWidth = ctx.measureText(label).width;
      const bckgDimensions = [textWidth, fontSize].map(n => n + fontSize * 0.5);
      ctx.fillStyle = isSelected ? 'rgba(139, 92, 246, 0.95)' : isNeighbor ? 'rgba(49, 46, 129, 0.9)' : 'rgba(0, 0, 0, 0.7)';
      ctx.fillRect(node.x - bckgDimensions[0] / 2, node.y + r + 3, bckgDimensions[0], bckgDimensions[1]);
      ctx.fillStyle = '#fff';
      ctx.fillText(label, node.x, node.y + r + 3 + bckgDimensions[1] / 2);
    }
  }, [selectedNode, neighborIds, devMode, highlightedSubject]);

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-6">
           <div className="relative">
              <Loader2 className="animate-spin text-primary" size={80} />
              <div className="absolute inset-0 bg-primary/20 blur-2xl rounded-full animate-pulse"></div>
           </div>
           <p className="text-muted-foreground font-black tracking-[0.4em] uppercase text-xs">Synchronizing Neural Vectors</p>
        </div>
      </div>
    );
  }

  if (!graphData || !graphData.nodes) {
    return (
      <div className="flex h-screen items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-4">
           <AlertTriangle className="text-destructive" size={48} />
           <p className="text-slate-500 font-bold uppercase tracking-widest text-xs">Failed to initialize Neural Plane</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 md:p-8 max-w-[1800px] w-full mx-auto relative h-screen flex flex-col overflow-hidden">
      <div className="flex flex-col md:flex-row justify-between items-center md:items-start mb-10 z-10 gap-6">
        <div className="flex items-center gap-5">
          <div className="p-4 bg-primary/10 rounded-3xl border border-primary/20 shadow-[0_0_40px_rgba(139,92,246,0.15)] group hover:scale-105 transition-transform duration-500">
             <LayoutGrid className="text-primary" size={32} />
          </div>
          <div>
            <h1 className="text-4xl font-black tracking-tighter text-white leading-none mb-2">Neural Plane</h1>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2 px-3 py-1 bg-success/10 border border-success/20 rounded-full">
                <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse"></span>
                <span className="text-[9px] text-success font-black uppercase tracking-widest">Live Link</span>
              </div>
              <p className="text-[10px] text-slate-500 font-bold uppercase tracking-[0.2em]">
                {graphData.total_nodes} Cards <span className="opacity-20 mx-1">/</span> {graphData.total_edges} Synapses
              </p>
            </div>
          </div>
        </div>
        
        <div className="flex flex-wrap items-center gap-3 pointer-events-auto">
          <button 
            onClick={handleConnectAll}
            disabled={tuningStatus.loading}
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-2xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-indigo-500/25 hover:shadow-indigo-500/40 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50"
            title="Automatically connect all concepts to form full neural graph"
          >
            <Sparkles size={14} className={tuningStatus.loading ? "animate-spin" : "animate-pulse"} />
            {tuningStatus.loading ? 'Connecting...' : 'Connect All Concepts'}
          </button>
          <button 
            onClick={() => setLockGraph(!lockGraph)}
            className={`md:hidden flex items-center gap-2 px-5 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all border ${lockGraph ? 'bg-primary text-white border-primary shadow-lg shadow-primary/20' : 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10 hover:text-white'}`}
          >
            {lockGraph ? 'Graph Locked' : 'Graph Unlocked'}
          </button>
          <button 
            onClick={() => setShowSettings(true)}
            className="flex items-center gap-2 px-5 py-2.5 bg-white/5 text-slate-400 border border-white/5 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-white/10 hover:text-white transition-all active:scale-95"
          >
            <Settings size={14} /> Neural Tuning
          </button>
          <button 
            onClick={() => setDevMode(!devMode)}
            className={`flex items-center gap-2 px-5 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-widest transition-all border ${devMode ? 'bg-primary text-primary-foreground border-primary shadow-lg shadow-primary/20' : 'bg-white/5 text-slate-400 border-white/5 hover:bg-white/10 hover:text-white'}`}
          >
            <Terminal size={14} /> {devMode ? 'Neural Debug: ON' : 'Debug Modes'}
          </button>
        </div>
      </div>

      <div className="flex-grow grid grid-cols-1 lg:grid-cols-[1fr_450px] gap-8 min-h-0 overflow-hidden pb-6">
        <div className="glass-card rounded-[3rem] border border-white/5 overflow-hidden relative shadow-2xl bg-black/40 h-full min-h-0">
          <div className="absolute inset-0 z-0">
             <ForceGraph2D
               ref={fgRef}
               graphData={data}
               backgroundColor="rgba(0,0,0,0)"
               nodeCanvasObject={drawNode}
               nodePointerAreaPaint={(node, color, ctx) => {
                 if (!isFinite(node.x) || !isFinite(node.y)) return;
                 const r = Math.sqrt(node.val) * 2.5;
                 ctx.fillStyle = color;
                 ctx.beginPath();
                 ctx.arc(node.x, node.y, r, 0, 2 * Math.PI, false);
                 ctx.fill();
               }}
               linkWidth={link => {
                 const sId = typeof link.source === 'object' ? link.source.id : link.source;
                 const tId = typeof link.target === 'object' ? link.target.id : link.target;
                 const selId = selectedNode?.concept_id || selectedNode?.id;

                 if (selId) {
                   return (sId === selId || tId === selId) ? 3.5 : 0.4;
                 }
                 if (!highlightedSubject || !graphData?.nodes) return 1.5;
                 const sNode = graphData.nodes.find(n => n.concept_id === sId);
                 const tNode = graphData.nodes.find(n => n.concept_id === tId);
                 return (sNode?.subject_id === highlightedSubject && tNode?.subject_id === highlightedSubject ? 3 : 0.5);
               }}
               linkColor={link => {
                 const sId = typeof link.source === 'object' ? link.source.id : link.source;
                 const tId = typeof link.target === 'object' ? link.target.id : link.target;
                 const selId = selectedNode?.concept_id || selectedNode?.id;

                 if (selId) {
                   return (sId === selId || tId === selId) 
                     ? 'rgba(168, 85, 247, 0.9)' 
                     : 'rgba(255, 255, 255, 0.02)';
                 }
                 if (!highlightedSubject || !graphData?.nodes) return 'rgba(139, 92, 246, 0.2)';
                 const sNode = graphData.nodes.find(n => n.concept_id === sId);
                 const tNode = graphData.nodes.find(n => n.concept_id === tId);
                 return (sNode?.subject_id === highlightedSubject && tNode?.subject_id === highlightedSubject) 
                   ? 'rgba(139, 92, 246, 0.6)' 
                   : 'rgba(255, 255, 255, 0.03)';
               }}
               linkDirectionalParticles={link => {
                 const sId = typeof link.source === 'object' ? link.source.id : link.source;
                 const tId = typeof link.target === 'object' ? link.target.id : link.target;
                 const selId = selectedNode?.concept_id || selectedNode?.id;

                 if (selId) {
                   return (sId === selId || tId === selId) ? 5 : 0;
                 }
                 if (!highlightedSubject || !graphData?.nodes) return 1;
                 const sNode = graphData.nodes.find(n => n.concept_id === sId);
                 return (sNode?.subject_id === highlightedSubject ? 4 : 0);
               }}
               linkDirectionalParticleSpeed={link => {
                 const sId = typeof link.source === 'object' ? link.source.id : link.source;
                 const tId = typeof link.target === 'object' ? link.target.id : link.target;
                 const selId = selectedNode?.concept_id || selectedNode?.id;
                 return (selId && (sId === selId || tId === selId)) ? 0.012 : 0.005;
               }}
               linkDirectionalParticleWidth={link => {
                 const sId = typeof link.source === 'object' ? link.source.id : link.source;
                 const tId = typeof link.target === 'object' ? link.target.id : link.target;
                 const selId = selectedNode?.concept_id || selectedNode?.id;
                 return (selId && (sId === selId || tId === selId)) ? 4 : 2;
               }}
               onNodeClick={handleNodeClick}
               onBackgroundClick={() => {
                 setHighlightedSubject(null);
                 setSelectedNode(null);
               }}
               cooldownTicks={150}
               enablePanInteraction={!lockGraph}
               enableZoomInteraction={!lockGraph}
             />
          </div>

          <div className="absolute bottom-10 left-10 flex flex-col gap-3 z-10 pointer-events-none text-white">
             {[
               { color: '#10b981', label: 'Consolidated' },
               { color: '#f59e0b', label: 'Unstable' },
               { color: '#f43f5e', label: 'Decaying' }
             ].map(item => (
               <div key={item.label} className="flex items-center gap-4 glass px-4 py-2 rounded-2xl border border-white/5 backdrop-blur-md">
                 <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }}></div>
                 <span className="text-[10px] font-black uppercase tracking-widest">{item.label}</span>
               </div>
             ))}
          </div>
        </div>

        <div className="flex flex-col gap-5 h-full min-h-0 overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/20 hover:scrollbar-thumb-primary/50 text-white">
          {selectedNode && (
            <div className="glass-card rounded-[2.5rem] border border-white/10 animate-in slide-in-from-right-12 duration-500 relative shadow-2xl flex flex-col min-h-0 overflow-hidden bg-slate-950/80 backdrop-blur-xl shrink-0">
              <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full -translate-y-32 translate-x-32 blur-[100px] pointer-events-none"></div>

              {/* Sticky Card Header */}
              <div className="p-6 border-b border-white/10 shrink-0 bg-white/[0.02]">
                <div className="flex justify-between items-start gap-4 mb-2">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-[9px] font-black uppercase tracking-[0.3em] text-primary">Node #{selectedNode.concept_id || selectedNode.id}</span>
                    <span className="px-2 py-0.5 rounded-md text-[8px] font-black uppercase tracking-wider bg-white/5 text-slate-400 border border-white/5">
                      {selectedNode.algorithm ? selectedNode.algorithm.toUpperCase() : 'FSRS'}
                    </span>
                    <span className="px-2 py-0.5 rounded-md text-[8px] font-black uppercase tracking-wider bg-primary/10 text-primary border border-primary/20">
                      {selectedNode.difficulty_level || 'MEDIUM'}
                    </span>
                  </div>

                  <button 
                    onClick={() => setSelectedNode(null)}
                    className="p-2 hover:bg-white/10 rounded-xl text-slate-400 hover:text-white transition-all shrink-0"
                    title="Close Details"
                  >
                    <X size={18} />
                  </button>
                </div>

                <h3 className="text-xl md:text-2xl font-black text-white tracking-tight leading-tight break-words">{selectedNode.title}</h3>
                <p className="text-[10px] uppercase font-bold tracking-[0.2em] text-slate-400 mt-1 flex items-center gap-2">
                  <Layers size={12} className="text-primary" /> {selectedNode.subject_name}
                </p>

                {/* Tab Navigation */}
                <div className="flex items-center gap-2 mt-4 p-1 bg-black/40 rounded-xl border border-white/5">
                  <button
                    onClick={() => setActiveDetailTab('card')}
                    className={`flex-1 py-1.5 px-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
                      activeDetailTab === 'card' 
                        ? 'bg-primary text-white shadow-md shadow-primary/25' 
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <BookOpen size={12} /> Card Content
                  </button>
                  <button
                    onClick={() => setActiveDetailTab('synapses')}
                    className={`flex-1 py-1.5 px-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
                      activeDetailTab === 'synapses' 
                        ? 'bg-primary text-white shadow-md shadow-primary/25' 
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <Network size={12} /> Synapses ({relatedConcepts.length})
                  </button>
                  <button
                    onClick={() => setActiveDetailTab('stats')}
                    className={`flex-1 py-1.5 px-2 rounded-lg text-[9px] font-black uppercase tracking-wider transition-all flex items-center justify-center gap-1.5 ${
                      activeDetailTab === 'stats' 
                        ? 'bg-primary text-white shadow-md shadow-primary/25' 
                        : 'text-slate-400 hover:text-white hover:bg-white/5'
                    }`}
                  >
                    <Zap size={12} /> Memory
                  </button>
                </div>
              </div>

              {/* Scrollable Tab Body */}
              <div className="p-6 space-y-5 max-h-[420px] overflow-y-auto pr-3 scrollbar-thin scrollbar-thumb-white/20 hover:scrollbar-thumb-primary/50">
                {activeDetailTab === 'card' && (
                  <div className="space-y-4">
                    {parsedContent ? (
                      <>
                        {parsedContent.front && (
                          <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/10 space-y-2">
                            <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-slate-400">
                              <HelpCircle size={13} className="text-primary" /> Flashcard Prompt (Question)
                            </div>
                            <div className="text-xs text-slate-100 font-medium leading-relaxed whitespace-pre-wrap">
                              {parsedContent.front}
                            </div>
                          </div>
                        )}

                        {parsedContent.back && (
                          <div className="p-4 bg-primary/[0.04] rounded-2xl border border-primary/20 space-y-3">
                            <div className="flex justify-between items-center">
                              <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-primary font-mono">
                                <BookOpen size={13} /> Target Solution & Code
                              </div>
                              <button
                                onClick={() => setShowSolution(!showSolution)}
                                className="flex items-center gap-1 text-[8px] font-bold uppercase tracking-wider px-2 py-1 bg-white/5 hover:bg-white/10 rounded-md text-slate-300 transition-colors"
                              >
                                {showSolution ? <EyeOff size={10} /> : <Eye size={10} />}
                                {showSolution ? 'Hide Solution' : 'Show Solution'}
                              </button>
                            </div>

                            {showSolution ? (
                              <div className="text-xs text-slate-200 font-normal leading-relaxed whitespace-pre-wrap animate-in fade-in duration-300">
                                {parsedContent.back.includes('```') ? (
                                  <div>
                                    {parsedContent.back.split('```').map((part, idx) => {
                                      if (idx % 2 === 1) {
                                        const lines = part.split('\n');
                                        const lang = lines[0].trim();
                                        const code = lines.slice(1).join('\n');
                                        return (
                                          <div key={idx} className="my-2 p-3.5 bg-black/80 rounded-xl border border-white/10 font-mono text-[11px] text-emerald-400 overflow-x-auto relative group">
                                            <div className="flex justify-between items-center mb-1 text-[8px] uppercase text-slate-500 font-bold border-b border-white/5 pb-1">
                                              <span>{lang || 'CODE'}</span>
                                              <button
                                                onClick={() => handleCopyCode(code || part)}
                                                className="hover:text-white transition-colors flex items-center gap-1 text-[8px]"
                                                title="Copy Code"
                                              >
                                                <Copy size={10} />
                                                {copiedCode ? 'Copied!' : 'Copy'}
                                              </button>
                                            </div>
                                            <pre className="overflow-x-auto">{code || part}</pre>
                                          </div>
                                        );
                                      }
                                      return <span key={idx}>{part}</span>;
                                    })}
                                  </div>
                                ) : (
                                  <p>{parsedContent.back}</p>
                                )}
                              </div>
                            ) : (
                              <button
                                onClick={() => setShowSolution(true)}
                                className="w-full py-6 rounded-xl border border-dashed border-primary/30 text-[10px] font-black uppercase tracking-widest text-primary hover:bg-primary/5 transition-all text-center flex flex-col items-center gap-2"
                              >
                                <Eye size={18} className="animate-pulse" />
                                Click to Reveal Target Solution & Code
                              </button>
                            )}
                          </div>
                        )}

                        {parsedContent.raw && !parsedContent.front && !parsedContent.back && (
                          <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/10 space-y-2">
                            <div className="flex items-center gap-2 text-[9px] font-black uppercase tracking-widest text-slate-400">
                              <FileText size={13} className="text-primary" /> Concept Content
                            </div>
                            <p className="text-xs text-slate-200 font-medium leading-relaxed whitespace-pre-wrap">
                              {parsedContent.raw}
                            </p>
                          </div>
                        )}
                      </>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No text content available for this node.</p>
                    )}

                    {/* Quick Synapses Bar */}
                    {relatedConcepts.length > 0 && (
                      <div className="p-4 bg-white/[0.02] rounded-2xl border border-white/5">
                        <div className="flex justify-between items-center mb-2">
                          <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Nearest Synapses</span>
                          <button 
                            onClick={() => setActiveDetailTab('synapses')}
                            className="text-[8px] font-black uppercase tracking-wider text-primary hover:underline"
                          >
                            View All ({relatedConcepts.length})
                          </button>
                        </div>
                        <div className="flex flex-wrap gap-1.5">
                          {relatedConcepts.slice(0, 4).map(c => (
                            <button
                              key={c.concept_id || c.id}
                              onClick={() => handleNodeClick(c)}
                              className="px-2.5 py-1 rounded-lg bg-white/5 hover:bg-primary/20 border border-white/5 text-[9px] font-bold text-slate-300 hover:text-white truncate max-w-[180px] transition-colors"
                            >
                              {c.title}
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {activeDetailTab === 'synapses' && (
                  <div className="space-y-3">
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-[9px] font-black uppercase tracking-[0.2em] text-slate-400">
                        {relatedConcepts.length} Interconnected Nodes
                      </span>
                      <span className="text-[8px] text-slate-500 font-bold">Click any card to jump</span>
                    </div>

                    {relatedConcepts.length === 0 ? (
                      <div className="p-6 bg-white/[0.02] rounded-2xl border border-white/5 text-center space-y-3">
                        <Network size={28} className="text-slate-600 mx-auto" />
                        <p className="text-xs text-slate-400 font-medium">No synapses currently linked to this concept.</p>
                        <button 
                          onClick={handleConnectAll}
                          className="px-4 py-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl text-[9px] font-black uppercase tracking-wider shadow-lg shadow-indigo-500/20 hover:scale-105 transition-all"
                        >
                          Synthesize All Synapses
                        </button>
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {relatedConcepts.map(neighbor => (
                          <button
                            key={neighbor.concept_id || neighbor.id}
                            onClick={() => handleNodeClick(neighbor)}
                            className="w-full p-3.5 rounded-2xl bg-white/[0.02] hover:bg-primary/20 border border-white/5 hover:border-primary/40 transition-all text-left group flex items-center justify-between gap-3 active:scale-[0.98]"
                          >
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <div className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: neighbor.color }}></div>
                                <span className="text-xs font-bold text-slate-200 group-hover:text-white truncate block">
                                  {neighbor.title}
                                </span>
                              </div>
                              <div className="flex items-center gap-2 text-[9px] text-slate-500 font-medium">
                                <span className="text-slate-400">{neighbor.subject_name}</span>
                                <span>•</span>
                                <span className="font-mono text-primary font-bold">{((neighbor.weight || 0.5) * 100).toFixed(0)}% Synaptic Weight</span>
                              </div>
                            </div>
                            <ChevronRight size={16} className="text-slate-500 group-hover:text-primary transition-transform group-hover:translate-x-1 shrink-0" />
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {activeDetailTab === 'stats' && (
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-3">
                      <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/5">
                        <span className="text-slate-500 text-[8px] font-black uppercase tracking-widest block mb-1">Memory Stability</span>
                        <span className="text-white font-mono font-black text-2xl">{selectedNode.stability?.toFixed(1) || '0.0'}d</span>
                        <p className="text-[8px] text-slate-500 mt-1">Days before retention drops below 90%</p>
                      </div>
                      <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/5">
                        <span className="text-slate-500 text-[8px] font-black uppercase tracking-widest block mb-1">Estimated Retention</span>
                        <span className={`font-mono font-black text-2xl ${(selectedNode.retrievability || 1) >= 0.85 ? 'text-success' : (selectedNode.retrievability || 1) >= 0.5 ? 'text-warning' : 'text-destructive'}`}>
                          {((selectedNode.retrievability || 1) * 100).toFixed(0)}%
                        </span>
                        <p className="text-[8px] text-slate-500 mt-1">Probability of successful recall</p>
                      </div>
                    </div>

                    <div className="p-4 bg-white/[0.03] rounded-2xl border border-white/5 space-y-3">
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Scheduling Algorithm</span>
                        <span className="font-bold font-mono text-primary uppercase">{selectedNode.algorithm || 'FSRS'}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Difficulty Rating</span>
                        <span className="font-bold text-white capitalize">{selectedNode.difficulty_level || 'Medium'}</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Review Repetitions</span>
                        <span className="font-bold font-mono text-white">{selectedNode.repetitions || 0} reviews</span>
                      </div>
                      <div className="flex justify-between items-center text-xs">
                        <span className="text-slate-400">Synaptic Degree</span>
                        <span className="font-bold font-mono text-white">{relatedConcepts.length} connected</span>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              {/* Bottom Actions Footer */}
              <div className="p-4 border-t border-white/10 shrink-0 bg-white/[0.02] flex items-center gap-3">
                <button 
                  onClick={() => navigate(`/study?concept=${selectedNode.concept_id}`)}
                  className="flex-1 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl text-[10px] font-black uppercase tracking-widest shadow-lg shadow-indigo-500/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  <Sparkles size={14} /> Practice Card
                </button>
                <button 
                  onClick={() => navigate(`/subjects/${selectedNode.subject_id}`)}
                  className="px-4 py-3 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-xl text-[10px] font-black uppercase tracking-widest border border-white/5 transition-all flex items-center justify-center gap-2"
                  title="Open in Subject Deck"
                >
                  <Maximize2 size={14} /> Deck
                </button>
              </div>
            </div>
          )}

          {/* Subject Clusters Card */}
          <div className="glass-card p-6 rounded-[2rem] border border-white/5 shadow-2xl shrink-0">
            <h3 className="text-[9px] font-black uppercase tracking-[0.4em] mb-4 text-slate-500 flex items-center gap-2">
              <Layers size={12} /> Subject Clusters
            </h3>
            <div className="space-y-2 max-h-[240px] overflow-y-auto pr-2 scrollbar-thin scrollbar-thumb-white/20">
              {subjects.map(sub => (
                <button
                  key={sub.id}
                  onClick={() => zoomToSubject(sub.id)}
                  className={`w-full p-3 rounded-xl border transition-all text-left group ${highlightedSubject === sub.id ? 'bg-primary/20 border-primary/40 shadow-[0_0_20px_rgba(139,92,246,0.1)]' : 'bg-white/[0.02] border-white/5 hover:bg-white/[0.08] hover:border-primary/30'}`}
                >
                  <div className="flex justify-between items-center">
                    <span className={`text-xs font-bold truncate pr-4 ${highlightedSubject === sub.id ? 'text-white' : 'text-slate-300 group-hover:text-white'}`}>{sub.name}</span>
                    <span className={`text-[9px] font-black px-2 py-0.5 rounded-md shrink-0 ${highlightedSubject === sub.id ? 'bg-primary text-white' : 'bg-primary/10 text-primary'}`}>{sub.count} Cards</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Global Telemetry Card */}
          <div className="glass-card p-6 rounded-[2rem] border border-white/5 shadow-2xl shrink-0">
            <h3 className="text-[9px] font-black uppercase tracking-[0.4em] mb-6 text-slate-500">Global Telemetry</h3>
            <div className="space-y-4">
               {[
                 { label: 'Overall Stability', val: (graphData.nodes?.reduce((acc, n) => acc + (n.stability || 0), 0) / (graphData.total_nodes || 1)).toFixed(1) + 'd', color: 'text-primary' },
                 { label: 'System Retention', val: (graphData.nodes?.reduce((acc, n) => acc + (n.retrievability || 0), 0) / (graphData.total_nodes || 1) * 100).toFixed(0) + '%', color: 'text-success' }
               ].map((stat, idx) => (
                 <div key={stat.label || idx} className="flex justify-between items-end">
                    <span className="text-[8px] font-black text-slate-500 uppercase tracking-widest">{stat.label}</span>
                    <span className={`font-mono font-black text-xl ${stat.color} leading-none`}>{stat.val}</span>
                 </div>
               ))}
            </div>
          </div>
        </div>
      </div>

      {showSettings && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-6 bg-black/60 backdrop-blur-sm animate-in fade-in duration-300">
          <div className="glass-card w-full max-w-2xl p-10 rounded-[3rem] border border-white/10 shadow-3xl animate-in zoom-in-95 duration-300 relative overflow-hidden">
            <div className="absolute top-0 right-0 w-96 h-96 bg-primary/5 rounded-full -translate-y-48 translate-x-48 blur-[120px]"></div>
            
            <div className="flex justify-between items-center mb-10">
              <div className="flex items-center gap-4">
                <div className="p-3 bg-primary/20 rounded-2xl border border-primary/30">
                  <Settings2 className="text-primary" size={24} />
                </div>
                <h2 className="text-2xl font-black tracking-tight text-white">Neural Engine Tuning</h2>
              </div>

              <button 
                onClick={() => { setShowSettings(false); setTuningStatus({ loading: false, message: '', type: '' }); setBridges(null); }}
                className="p-2 hover:bg-white/5 rounded-xl text-slate-500 hover:text-white transition-all"
              >
                <RotateCcw size={20} />
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10">
              <div className="p-6 bg-white/[0.03] rounded-[2rem] border border-white/5 hover:border-primary/20 transition-all group">
                <div className="flex items-center gap-3 mb-4">
                  <Cpu size={18} className="text-primary opacity-50 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Memory Physics</span>
                </div>
                <h3 className="text-sm font-bold text-white mb-2">FSRS Parameter Tuning</h3>
                <p className="text-[10px] text-slate-500 leading-relaxed mb-6">Re-align the Spaced Repetition core based on your historical recall patterns.</p>
                <button 
                  onClick={handleOptimizeFsrs}
                  disabled={tuningStatus.loading}
                  className="w-full py-3 bg-white/5 hover:bg-primary hover:text-primary-foreground text-slate-300 rounded-xl text-[9px] font-black uppercase tracking-widest border border-white/5 transition-all disabled:opacity-50"
                >
                  Optimize FSRS
                </button>
              </div>

              <div className="p-6 bg-white/[0.03] rounded-[2rem] border border-white/5 hover:border-purple-500/20 transition-all group">
                <div className="flex items-center gap-3 mb-4">
                  <Zap size={18} className="text-purple-500 opacity-50 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Synaptic Weighting</span>
                </div>
                <h3 className="text-sm font-bold text-white mb-2">Neural Weight Balance</h3>
                <p className="text-[10px] text-slate-500 leading-relaxed mb-6">Heuristically adjust Expert vs. Data influence for knowledge propagation.</p>
                <button 
                  onClick={handleTuneWeights}
                  disabled={tuningStatus.loading}
                  className="w-full py-3 bg-white/5 hover:bg-purple-600 hover:text-white text-slate-300 rounded-xl text-[9px] font-black uppercase tracking-widest border border-white/5 transition-all disabled:opacity-50"
                >
                  Balance Weights
                </button>
              </div>

              <div className="p-6 bg-white/[0.03] rounded-[2rem] border border-white/5 hover:border-accent/20 transition-all group md:col-span-2">
                <div className="flex items-center gap-3 mb-4">
                  <Sparkles size={18} className="text-accent opacity-50 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Intelligence Layer</span>
                </div>
                <div className="flex justify-between items-start gap-10">
                   <div className="flex-1">
                      <h3 className="text-sm font-bold text-white mb-2">Neural Bridge Discovery</h3>
                      <p className="text-[10px] text-slate-500 leading-relaxed">AI analyzes disconnected concept islands and suggests semantic bridges to unify your graph.</p>
                   </div>
                   <button 
                    onClick={handleSuggestBridges}
                    disabled={tuningStatus.loading}
                    className="px-8 py-3 bg-accent text-white rounded-xl text-[9px] font-black uppercase tracking-widest shadow-lg shadow-accent/20 hover:scale-105 active:scale-95 transition-all disabled:opacity-50"
                  >
                    Suggest Bridges
                  </button>
                </div>
              </div>

              <div className="p-6 bg-white/[0.03] rounded-[2rem] border border-white/5 hover:border-indigo-500/20 transition-all group md:col-span-2">
                <div className="flex items-center gap-3 mb-4">
                  <Sparkles size={18} className="text-indigo-400 opacity-50 group-hover:opacity-100 transition-opacity" />
                  <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">Synaptic Matrix</span>
                </div>
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-6">
                   <div className="flex-1">
                      <h3 className="text-sm font-bold text-white mb-2">Connect All Concepts (Auto-Link Matrix)</h3>
                      <p className="text-[10px] text-slate-500 leading-relaxed">Runs semantic clustering and topic topology to connect every single card into a multi-connected neural knowledge graph.</p>
                   </div>
                   <button 
                    onClick={handleConnectAll}
                    disabled={tuningStatus.loading}
                    className="px-8 py-3 bg-gradient-to-r from-violet-600 to-indigo-600 text-white rounded-xl text-[9px] font-black uppercase tracking-widest shadow-lg shadow-indigo-500/20 hover:scale-105 active:scale-95 transition-all disabled:opacity-50 shrink-0"
                  >
                    {tuningStatus.loading ? 'Connecting...' : 'Connect All Concepts'}
                  </button>
                </div>
              </div>
            </div>
{/* Status / Output */}
{tuningStatus.message && (
  <div className={`p-4 rounded-2xl flex items-center gap-3 animate-in slide-in-from-bottom-2 duration-300 ${tuningStatus.type === 'success' ? 'bg-success/10 text-success border border-success/20' : tuningStatus.type === 'error' ? 'bg-destructive/10 text-destructive border border-destructive/20' : 'bg-primary/10 text-primary border border-primary/20'}`}>
    {tuningStatus.loading ? <Loader2 size={16} className="animate-spin" /> : tuningStatus.type === 'success' ? <Check size={16} /> : <AlertCircle size={16} />}
    <span className="text-[11px] font-bold uppercase tracking-wider">{tuningStatus.message}</span>
  </div>
)}


            {bridges && (
              <div className="mt-6 p-6 bg-white/[0.02] rounded-3xl border border-white/5 space-y-3 animate-in fade-in duration-500">
                <h4 className="text-[9px] font-black uppercase tracking-widest text-slate-500">Bridge Prototypes identified:</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {bridges.map((b, i) => (
                    <div key={i} className="p-3 bg-white/5 rounded-xl border border-white/5 text-[11px] font-bold text-white flex items-center gap-3">
                      <div className="w-1.5 h-1.5 rounded-full bg-accent"></div> {b}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default KnowledgeGraph;
