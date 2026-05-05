import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Loader2, Network, ZoomIn, ZoomOut, RotateCcw, Info } from 'lucide-react';
import api from '../api';

const KnowledgeGraph = () => {
  const [graphData, setGraphData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState(null);
  const [hoveredNode, setHoveredNode] = useState(null);
  const canvasRef = useRef(null);
  const [transform, setTransform] = useState({ x: 0, y: 0, scale: 1 });
  const [dragging, setDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [nodePositions, setNodePositions] = useState({});

  useEffect(() => {
    const fetchGraph = async () => {
      try {
        const res = await api.get('/graph/full');
        setGraphData(res.data);
        if (res.data.nodes.length > 0) {
          layoutNodes(res.data);
        }
      } catch (err) {
        console.error('Failed to load graph', err);
      } finally {
        setLoading(false);
      }
    };
    fetchGraph();
  }, []);

  const layoutNodes = (data) => {
    // Force-directed-like circular layout with subject grouping
    const nodes = data.nodes;
    const positions = {};
    const centerX = 400;
    const centerY = 300;
    const radius = Math.max(150, nodes.length * 25);

    // Group by subject
    const subjects = {};
    nodes.forEach((n) => {
      if (!subjects[n.subject_name]) subjects[n.subject_name] = [];
      subjects[n.subject_name].push(n);
    });

    let globalIdx = 0;
    const subjectKeys = Object.keys(subjects);
    subjectKeys.forEach((subj, si) => {
      const subjectAngle = (2 * Math.PI * si) / subjectKeys.length;
      const subjectCenterX = centerX + radius * 0.5 * Math.cos(subjectAngle);
      const subjectCenterY = centerY + radius * 0.5 * Math.sin(subjectAngle);
      const group = subjects[subj];

      group.forEach((node, ni) => {
        const angle = (2 * Math.PI * ni) / group.length + subjectAngle;
        const r = 80 + group.length * 15;
        positions[node.concept_id] = {
          x: subjectCenterX + r * Math.cos(angle),
          y: subjectCenterY + r * Math.sin(angle),
        };
        globalIdx++;
      });
    });

    setNodePositions(positions);
  };

  const getNodeColor = (node) => {
    if (node.retrievability >= 0.85) return '#22c55e'; // green — strong
    if (node.retrievability >= 0.5) return '#f59e0b';  // amber — ok
    return '#ef4444'; // red — weak
  };

  const getNodeRadius = (node) => {
    return 12 + Math.min(node.neighbor_count * 4, 20);
  };

  const drawGraph = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !graphData) return;
    const ctx = canvas.getContext('2d');
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, rect.width, rect.height);

    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.scale, transform.scale);

    // Draw edges
    graphData.edges.forEach((edge) => {
      const from = nodePositions[edge.source_concept_id];
      const to = nodePositions[edge.target_concept_id];
      if (!from || !to) return;

      const alpha = Math.max(0.15, edge.w_final);
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.strokeStyle = `rgba(139, 92, 246, ${alpha})`;
      ctx.lineWidth = 1 + edge.w_final * 3;
      ctx.stroke();

      // Edge weight label at midpoint
      if (edge.w_final > 0.3) {
        const mx = (from.x + to.x) / 2;
        const my = (from.y + to.y) / 2;
        ctx.fillStyle = 'rgba(148, 163, 184, 0.6)';
        ctx.font = '10px Inter, sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(edge.w_final.toFixed(2), mx, my - 4);
      }
    });

    // Draw nodes
    graphData.nodes.forEach((node) => {
      const pos = nodePositions[node.concept_id];
      if (!pos) return;
      const r = getNodeRadius(node);
      const isHovered = hoveredNode === node.concept_id;
      const isSelected = selectedNode?.concept_id === node.concept_id;

      // Glow effect
      if (isHovered || isSelected) {
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, r + 8, 0, 2 * Math.PI);
        const glow = ctx.createRadialGradient(pos.x, pos.y, r, pos.x, pos.y, r + 8);
        glow.addColorStop(0, getNodeColor(node) + '60');
        glow.addColorStop(1, 'transparent');
        ctx.fillStyle = glow;
        ctx.fill();
      }

      // Node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, r, 0, 2 * Math.PI);
      ctx.fillStyle = getNodeColor(node);
      ctx.fill();
      ctx.strokeStyle = isSelected ? '#fff' : 'rgba(255,255,255,0.3)';
      ctx.lineWidth = isSelected ? 3 : 1;
      ctx.stroke();

      // Label
      ctx.fillStyle = '#fff';
      ctx.font = `${isHovered ? 'bold ' : ''}11px Inter, sans-serif`;
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      const label = node.title.length > 18 ? node.title.substring(0, 16) + '…' : node.title;
      ctx.fillText(label, pos.x, pos.y + r + 5);
    });

    ctx.restore();
  }, [graphData, nodePositions, transform, hoveredNode, selectedNode]);

  useEffect(() => {
    drawGraph();
  }, [drawGraph]);

  const handleCanvasClick = (e) => {
    if (!graphData) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = (e.clientX - rect.left - transform.x) / transform.scale;
    const my = (e.clientY - rect.top - transform.y) / transform.scale;

    for (const node of graphData.nodes) {
      const pos = nodePositions[node.concept_id];
      if (!pos) continue;
      const r = getNodeRadius(node);
      const dist = Math.sqrt((mx - pos.x) ** 2 + (my - pos.y) ** 2);
      if (dist <= r + 5) {
        setSelectedNode(node);
        return;
      }
    }
    setSelectedNode(null);
  };

  const handleCanvasMouseMove = (e) => {
    if (dragging) {
      setTransform((prev) => ({
        ...prev,
        x: prev.x + (e.clientX - dragStart.x),
        y: prev.y + (e.clientY - dragStart.y),
      }));
      setDragStart({ x: e.clientX, y: e.clientY });
      return;
    }

    if (!graphData) return;
    const rect = canvasRef.current.getBoundingClientRect();
    const mx = (e.clientX - rect.left - transform.x) / transform.scale;
    const my = (e.clientY - rect.top - transform.y) / transform.scale;

    let found = null;
    for (const node of graphData.nodes) {
      const pos = nodePositions[node.concept_id];
      if (!pos) continue;
      const r = getNodeRadius(node);
      if (Math.sqrt((mx - pos.x) ** 2 + (my - pos.y) ** 2) <= r + 5) {
        found = node.concept_id;
        break;
      }
    }
    setHoveredNode(found);
    canvasRef.current.style.cursor = found ? 'pointer' : dragging ? 'grabbing' : 'grab';
  };

  const zoom = (factor) => {
    setTransform((prev) => ({
      ...prev,
      scale: Math.max(0.3, Math.min(3, prev.scale * factor)),
    }));
  };

  const resetView = () => {
    setTransform({ x: 0, y: 0, scale: 1 });
    setSelectedNode(null);
  };

  if (loading) {
    return (
      <div className="p-8 flex justify-center">
        <Loader2 className="animate-spin text-purple-400" size={48} />
      </div>
    );
  }

  if (!graphData || graphData.total_nodes === 0) {
    return (
      <div className="p-8 max-w-4xl w-full mx-auto mt-12 text-center">
        <div className="glass p-16 rounded-3xl inline-flex flex-col items-center">
          <Network size={80} className="text-slate-500 mb-6" />
          <h1 className="text-4xl font-bold mb-4">No Knowledge Graph Yet</h1>
          <p className="text-slate-400 text-lg max-w-md">
            Create concepts with parent relationships or use the AI Tutor's "Optimize Graph" to auto-connect your concepts.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-[1400px] w-full">
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-4xl font-bold flex items-center gap-3">
            <Network className="text-purple-400" size={36} /> Knowledge Graph
          </h1>
          <p className="text-slate-400 mt-1">
            {graphData.total_nodes} concepts · {graphData.total_edges} connections
          </p>
        </div>
        <div className="flex gap-2">
          <button onClick={() => zoom(1.2)} className="p-2 glass rounded-lg hover:bg-white/10 transition-colors" title="Zoom In">
            <ZoomIn size={20} />
          </button>
          <button onClick={() => zoom(0.8)} className="p-2 glass rounded-lg hover:bg-white/10 transition-colors" title="Zoom Out">
            <ZoomOut size={20} />
          </button>
          <button onClick={resetView} className="p-2 glass rounded-lg hover:bg-white/10 transition-colors" title="Reset View">
            <RotateCcw size={20} />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-[1fr_320px] gap-6">
        {/* Canvas */}
        <div className="glass rounded-3xl border border-white/10 overflow-hidden relative" style={{ height: '600px' }}>
          <canvas
            ref={canvasRef}
            className="w-full h-full"
            onClick={handleCanvasClick}
            onMouseMove={handleCanvasMouseMove}
            onMouseDown={(e) => { setDragging(true); setDragStart({ x: e.clientX, y: e.clientY }); }}
            onMouseUp={() => setDragging(false)}
            onMouseLeave={() => { setDragging(false); setHoveredNode(null); }}
            onWheel={(e) => { e.preventDefault(); zoom(e.deltaY < 0 ? 1.1 : 0.9); }}
          />
          {/* Legend */}
          <div className="absolute bottom-4 left-4 glass rounded-xl p-3 text-xs text-slate-400 flex gap-4">
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-green-500 inline-block"></span> R ≥ 0.85</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-amber-500 inline-block"></span> R ≥ 0.50</span>
            <span className="flex items-center gap-1.5"><span className="w-3 h-3 rounded-full bg-red-500 inline-block"></span> R &lt; 0.50</span>
          </div>
        </div>

        {/* Detail Panel */}
        <div className="flex flex-col gap-4">
          {selectedNode ? (
            <div className="glass rounded-2xl p-6 border border-white/10">
              <h3 className="text-xl font-bold text-white mb-1 truncate">{selectedNode.title}</h3>
              <p className="text-sm text-slate-400 mb-4">{selectedNode.subject_name}</p>

              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Stability (S)</span>
                  <span className="text-white font-mono font-bold">{selectedNode.stability.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Difficulty (D)</span>
                  <span className="text-white font-mono font-bold">{selectedNode.difficulty.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Retrievability (R)</span>
                  <span className={`font-mono font-bold ${selectedNode.retrievability >= 0.85 ? 'text-green-400' : selectedNode.retrievability >= 0.5 ? 'text-amber-400' : 'text-red-400'}`}>
                    {(selectedNode.retrievability * 100).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Interval</span>
                  <span className="text-white font-mono font-bold">{selectedNode.interval_days}d</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-400 text-sm">Connections</span>
                  <span className="text-purple-400 font-mono font-bold">{selectedNode.neighbor_count}</span>
                </div>
              </div>

              {/* Retrievability bar */}
              <div className="mt-4">
                <div className="h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{
                      width: `${selectedNode.retrievability * 100}%`,
                      background: selectedNode.retrievability >= 0.85
                        ? 'linear-gradient(to right, #22c55e, #4ade80)'
                        : selectedNode.retrievability >= 0.5
                        ? 'linear-gradient(to right, #f59e0b, #fbbf24)'
                        : 'linear-gradient(to right, #ef4444, #f87171)',
                    }}
                  />
                </div>
              </div>
            </div>
          ) : (
            <div className="glass rounded-2xl p-6 border border-white/10 text-center">
              <Info size={32} className="mx-auto text-slate-500 mb-3" />
              <p className="text-slate-400 text-sm">Click a node to see its details</p>
            </div>
          )}

          {/* Graph Stats */}
          <div className="glass rounded-2xl p-6 border border-white/10">
            <h3 className="text-lg font-bold mb-3">Graph Health</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Strong (R ≥ 0.85)</span>
                <span className="text-green-400 font-bold">
                  {graphData.nodes.filter(n => n.retrievability >= 0.85).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">At Risk (R ≥ 0.5)</span>
                <span className="text-amber-400 font-bold">
                  {graphData.nodes.filter(n => n.retrievability >= 0.5 && n.retrievability < 0.85).length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Weak (R &lt; 0.5)</span>
                <span className="text-red-400 font-bold">
                  {graphData.nodes.filter(n => n.retrievability < 0.5).length}
                </span>
              </div>
              <div className="flex justify-between border-t border-white/10 pt-2 mt-2">
                <span className="text-slate-400">Avg Connections</span>
                <span className="text-purple-400 font-bold">
                  {graphData.total_nodes > 0 
                    ? (graphData.total_edges / graphData.total_nodes).toFixed(1) 
                    : '0'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default KnowledgeGraph;
