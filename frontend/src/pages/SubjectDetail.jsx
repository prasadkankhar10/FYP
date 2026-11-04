import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'framer-motion';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { Plus, BrainCircuit, Loader2, ArrowLeft, Trash2, Edit2, Search, Filter, Play, Zap, Info, MoreVertical, LayoutGrid, List, Code2, Timer, X, Calendar, Clock, Trophy, Sparkles } from 'lucide-react';
import api, { showToast } from '../api';
import ReactMarkdown from 'react-markdown';
import CodeEditor from './CodeEditor';

const SubjectDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [subject, setSubject] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [schedMap, setSchedMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [viewMode, setViewMode] = useState('grid'); // grid | list
  
  const [newTitle, setNewTitle] = useState('');
  const [newFrontMsg, setNewFrontMsg] = useState('');
  const [newBackMsg, setNewBackMsg] = useState('');
  const [codeSnippet, setCodeSnippet] = useState('');
  const [showCodeInput, setShowCodeInput] = useState(false);
  const [editingConcept, setEditingConcept] = useState(null);
  const [parentConceptId, setParentConceptId] = useState('');

  // Exam Protocol State
  const [examDate, setExamDate] = useState('');
  const [isUpdatingExamDate, setIsUpdatingExamDate] = useState(false);
  const [showRecapModal, setShowRecapModal] = useState(false);
  const [recapMarkdown, setRecapMarkdown] = useState('');
  const [loadingRecap, setLoadingRecap] = useState(false);

  const fetchData = async () => {
    try {
      const subRes = await api.get('/subjects/');
      const currentSub = subRes.data.find(s => s.id === parseInt(id));
      if (currentSub) {
        setSubject(currentSub);
        if (currentSub.exam_date) {
          setExamDate(new Date(currentSub.exam_date).toISOString().split('T')[0]);
        }
      }

      const conceptRes = await api.get(`/concepts/?subject_id=${id}`);
      const fetchedConcepts = conceptRes.data;
      setConcepts(fetchedConcepts);

      const schedData = {};
      await Promise.all(
        fetchedConcepts.map(async (c) => {
          try {
            const sRes = await api.get(`/schedule/${c.id}`);
            schedData[c.id] = sRes.data;
          } catch { /* no sched data */ }
        })
      );
      setSchedMap(schedData);
    } catch (err) {
      showToast("Failed to sync subject data", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const filteredConcepts = useMemo(() => {
    return concepts.filter(c => 
      c.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (c.content && c.content.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [concepts, searchTerm]);

  const handleUpdateExamDate = async (newDate) => {
    setExamDate(newDate);
    setIsUpdatingExamDate(true);
    try {
      await api.put(`/subjects/${id}`, { exam_date: newDate ? new Date(newDate).toISOString() : null });
      showToast("Exam date synchronized", "success");
      fetchData();
    } catch (err) {
      showToast("Failed to update exam protocol", "error");
    } finally {
      setIsUpdatingExamDate(false);
    }
  };

  const getExamCountdown = () => {
    if (!subject?.exam_date) return null;
    const diff = new Date(subject.exam_date) - new Date();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    if (days < 0) return "Terminated";
    if (days === 0) return "T-Minus: TODAY";
    return `T-Minus: ${days} Day${days > 1 ? 's' : ''}`;
  };

  const handleGenerateRecap = async () => {
    setLoadingRecap(true);
    setShowRecapModal(true);
    setRecapMarkdown('');
    try {
      const res = await api.get(`/ai/exam-recap/${id}`);
      setRecapMarkdown(res.data.recap_markdown);
    } catch (err) {
      showToast("Logic engine failed to synthesize recap", "error");
      setShowRecapModal(false);
    } finally {
      setLoadingRecap(false);
    }
  };

  const startCramMode = () => {
    navigate(`/study?exam_subject_id=${id}`);
  };

  const handleSubmitConcept = async (e) => {
    e.preventDefault();
    let backContent = newBackMsg;
    if (codeSnippet.trim()) {
      const lang = subject?.name?.toLowerCase().includes('c++') ? 'cpp' : 'javascript';
      backContent = `${newBackMsg}\n\n\`\`\`${lang}\n${codeSnippet}\n\`\`\``;
    }
    const finalContent = JSON.stringify({ front: newFrontMsg, back: backContent });

    try {
      if (editingConcept) {
        await api.put(`/concepts/${editingConcept.id}`, { 
          title: newTitle, 
          content: finalContent,
          parent_concept_id: parentConceptId ? parseInt(parentConceptId) : null
        });
        showToast("Card updated", "success");
      } else {
        await api.post('/concepts/', { 
          subject_id: parseInt(id), 
          title: newTitle, 
          content: finalContent, 
          parent_concept_id: parentConceptId ? parseInt(parentConceptId) : null 
        });
        showToast("Card created", "success");
      }
      setShowModal(false);
      setEditingConcept(null);
      setNewTitle('');
      setNewFrontMsg('');
      setNewBackMsg('');
      setCodeSnippet('');
      setShowCodeInput(false);
      setParentConceptId('');
      fetchData();
    } catch (err) {
      showToast("Failed to save changes", "error");
    }
  };

  const openAddModal = () => {
    setEditingConcept(null);
    setNewTitle('');
    setNewFrontMsg('');
    setNewBackMsg('');
    setCodeSnippet('');
    setShowCodeInput(false);
    setParentConceptId('');
    setShowModal(true);
  };

  const openEditModal = (concept) => {
    setEditingConcept(concept);
    setNewTitle(concept.title);
    setParentConceptId(concept.parent_concept_id || '');
    let parsedFront = '';
    let parsedBack = concept.content;
    try {
      if (concept.content && concept.content.trim().startsWith('{')) {
        const parsed = JSON.parse(concept.content);
        if (parsed.front !== undefined && parsed.back !== undefined) {
          parsedFront = parsed.front;
          parsedBack = parsed.back;
        }
      }
    } catch (e) { parsedFront = ''; }
    setNewFrontMsg(parsedFront);
    const codeMatch = parsedBack.match(/```(?:\w+)?\n([\s\S]*?)\n```/);
    if (codeMatch) {
      setCodeSnippet(codeMatch[1]);
      setNewBackMsg(parsedBack.replace(/```(?:\w+)?\n[\s\S]*?\n```/, '').trim());
      setShowCodeInput(true);
    } else {
      setCodeSnippet('');
      setNewBackMsg(parsedBack);
      setShowCodeInput(false);
    }
    setShowModal(true);
  };

  const handleDelete = async (conceptId) => {
    if (!window.confirm("Delete this concept?")) return;
    try {
      await api.delete(`/concepts/${conceptId}`);
      showToast("Card removed", "info");
      fetchData();
    } catch (err) {
      showToast("Deletion failed", "error");
    }
  };

  const getRetColor = (r) => {
    if (r >= 0.85) return 'text-success';
    if (r >= 0.5) return 'text-warning';
    return 'text-destructive';
  };

  if (loading) return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-primary" size={48} /></div>;
  if (!subject) return <div className="p-8 text-center"><h2 className="text-2xl font-bold mb-4">Subject not found</h2><Link to="/subjects" className="text-primary hover:underline">Return to Subjects</Link></div>;

  return (
    <div className="p-4 md:p-8 max-w-7xl w-full mx-auto animate-in fade-in duration-700">
      <div className="mb-12">
        <Link to="/subjects" className="text-muted-foreground hover:text-foreground flex items-center gap-2 w-fit mb-8 transition-colors group">
          <ArrowLeft size={18} className="group-hover:-translate-x-1 transition-transform" /> Back to Knowledge Base
        </Link>
        
        <div className="flex flex-col lg:flex-row justify-between items-start gap-8">
          <div className="max-w-3xl">
            <div className="flex items-center gap-3 mb-4">
               <div className="p-2 bg-primary/10 rounded-lg border border-primary/20">
                  <BrainCircuit className="text-primary" size={20} />
               </div>
               <span className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Domain View</span>
            </div>
            <h1 className="text-5xl md:text-6xl font-black tracking-tighter mb-4 text-white">{subject.name}</h1>
            <p className="text-slate-400 text-lg md:text-xl leading-relaxed font-medium">{subject.description}</p>
          </div>
          <div className="flex flex-wrap gap-3 w-full md:w-auto">
            <button 
              onClick={() => navigate(`/study?subject_id=${id}`)}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-gradient-to-r from-violet-600 to-indigo-600 text-white px-7 py-4 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 active:scale-95 transition-all shadow-xl shadow-indigo-500/20"
            >
              <Play size={16} className="fill-current" /> Study Subject
            </button>
            <button 
              onClick={startCramMode}
              className="flex-1 md:flex-none flex items-center justify-center gap-2 bg-amber-500/10 text-amber-500 px-6 py-4 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-amber-500 hover:text-white transition-all border border-amber-500/20 shadow-xl shadow-amber-500/10"
            >
              <Zap size={18} className="fill-current" /> Logic Blitz (Cram)
            </button>
            <button 
              onClick={openAddModal}
              className="hidden md:flex items-center justify-center gap-2 bg-white/10 hover:bg-white/15 px-6 py-4 rounded-2xl text-white font-black text-xs uppercase tracking-widest hover:opacity-90 transition-all border border-white/5"
            >
              <Plus size={20} /> New Card
            </button>
          </div>
        </div>
      </div>

      {/* Mobile FAB */}
      <button 
        onClick={openAddModal}
        className="md:hidden fixed bottom-28 right-6 z-40 w-14 h-14 bg-primary text-primary-foreground rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:scale-105 active:scale-95 transition-all"
      >
        <Plus size={28} />
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-8 mb-12">
        <div className="lg:col-span-3">
           <div className="flex flex-col md:flex-row gap-4">
              <div className="relative flex-1 group">
                <Search className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-500 group-focus-within:text-primary transition-colors" size={18} />
                <input 
                  type="text"
                  placeholder="Search synaptic cards..."
                  className="w-full bg-white/[0.03] border border-white/10 rounded-2xl pl-14 pr-6 py-4 text-white focus:ring-4 focus:ring-primary/10 outline-none transition-all hover:bg-white/[0.05]"
                  value={searchTerm}
                  onChange={e => setSearchTerm(e.target.value)}
                />
              </div>
              <div className="flex gap-2">
                <button onClick={() => setViewMode(viewMode === 'grid' ? 'list' : 'grid')} className="flex items-center gap-2 px-5 py-4 rounded-2xl glass hover:bg-white/5 transition-colors border border-white/5">
                  {viewMode === 'grid' ? <List size={20} className="text-slate-400" /> : <LayoutGrid size={20} className="text-slate-400" />}
                </button>
                <button className="flex items-center gap-2 px-5 py-4 rounded-2xl glass hover:bg-white/5 transition-colors border border-white/5 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  <Filter size={18} /> Filter
                </button>
              </div>
           </div>
        </div>

        <div className="glass-card p-6 rounded-[2rem] border border-white/5 relative overflow-hidden group">
           <div className={`absolute top-0 right-0 w-24 h-24 rounded-full blur-2xl transition-all ${subject?.exam_date ? 'bg-amber-500/10 opacity-100' : 'bg-primary/5 opacity-0'}`}></div>
           <div className="flex flex-col gap-4 relative z-10">
              <div className="flex items-center justify-between">
                 <div className="flex items-center gap-2 text-slate-500">
                    <Calendar size={14} />
                    <span className="text-[9px] font-black uppercase tracking-widest">Exam Protocol</span>
                 </div>
                 {subject?.exam_date && (
                    <span className={`text-[8px] font-black px-2 py-0.5 rounded uppercase tracking-tighter ${getExamCountdown() === 'Terminated' ? 'bg-destructive/20 text-destructive' : 'bg-amber-500/20 text-amber-500'}`}>
                       {getExamCountdown()}
                    </span>
                 )}
              </div>
              
              <div className="relative">
                 <input type="date" className="w-full bg-white/5 border border-white/10 rounded-xl px-4 py-3 text-white text-xs font-bold focus:ring-2 focus:ring-primary outline-none transition-all [color-scheme:dark]" value={examDate} onChange={(e) => handleUpdateExamDate(e.target.value)} />
                 {isUpdatingExamDate && <Loader2 className="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-primary" size={14} />}
              </div>
              <button onClick={handleGenerateRecap} className="w-full py-3 bg-primary/10 text-primary border border-primary/20 rounded-xl text-[9px] font-black uppercase tracking-widest hover:bg-primary hover:text-white transition-all flex items-center justify-center gap-2">
                <Sparkles size={12} /> Pre-Exam Recap
              </button>
              <p className="text-[9px] text-slate-600 font-medium leading-tight">Set your deadline to activate specialized high-intensity neural re-routing.</p>
           </div>
        </div>
      </div>

      {concepts.length === 0 ? (
        <div className="glass-card p-20 rounded-[3rem] text-center border-dashed border border-white/10">
          <div className="p-8 bg-white/5 rounded-full w-fit mx-auto mb-8 border border-white/5"><BrainCircuit size={64} className="text-slate-600 opacity-40" /></div>
          <h3 className="text-3xl font-black mb-4 text-white tracking-tight">Empty Knowledge Domain</h3>
          <p className="text-slate-500 max-w-md mx-auto font-medium leading-relaxed mb-10 uppercase text-[10px] tracking-widest">This sector is currently offline. Initialize your first card to begin building your neural network.</p>
          <button onClick={openAddModal} className="bg-primary text-primary-foreground px-10 py-4 rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 transition-all">Add First Card</button>
        </div>
      ) : (
        <div className={viewMode === 'grid' ? "grid grid-cols-1 md:grid-cols-2 gap-8" : "flex flex-col gap-4"}>
          {filteredConcepts.map(concept => {
            const sched = schedMap[concept.id];
            return (
              <div key={concept.id} className="glass-card p-8 md:p-10 rounded-[2.5rem] flex flex-col group transition-all hover:border-primary/20 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-16 translate-x-16 blur-3xl opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="flex justify-between items-start mb-8 relative z-10">
                  <div className="flex-1 min-w-0">
                    <h4 className="text-2xl md:text-3xl font-black text-white truncate mb-3 group-hover:text-primary transition-colors tracking-tight">{concept.title}</h4>
                    <div className="flex items-center gap-4 flex-wrap">
                      <span className="bg-primary/20 text-primary px-3 py-1 rounded-lg font-black uppercase text-[9px] tracking-[0.2em] border border-primary/20">{sched?.algorithm || 'SYNCHRONIZING'}</span>
                      <span className="text-[10px] font-bold text-slate-500 flex items-center gap-2 uppercase tracking-widest"><Timer size={14} className="opacity-50" />Next Sync: <span className="text-slate-300">{concept.next_review_date ? new Date(concept.next_review_date + 'Z').toLocaleDateString() : 'IMMEDIATE'}</span></span>
                    </div>
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-all">
                    <button onClick={() => openEditModal(concept)} className="p-3 glass rounded-xl text-slate-400 hover:text-white hover:bg-white/10 border border-white/5"><Edit2 size={18} /></button>
                    <button onClick={() => handleDelete(concept.id)} className="p-3 glass rounded-xl text-slate-400 hover:text-destructive hover:bg-destructive/10 border border-white/5"><Trash2 size={18} /></button>
                  </div>
                </div>
                <div className="prose prose-invert prose-sm max-w-none line-clamp-3 mb-10 text-slate-400 text-lg leading-relaxed font-medium relative z-10"><ReactMarkdown>{concept.content}</ReactMarkdown></div>
                {sched && (
                  <div className="grid grid-cols-4 gap-6 pt-8 border-t border-white/5 relative z-10">
                    {[
                      { label: 'Stability', val: `${sched.stability?.toFixed(1)}d` },
                      { label: 'Complexity', val: `D${sched.difficulty_fsrs?.toFixed(1)}` },
                      { label: 'Retention', val: sched.retrievability != null ? (sched.retrievability * 100).toFixed(0) + '%' : '—', color: getRetColor(sched.retrievability ?? 1) },
                      { label: 'Interval', val: `${sched.interval_days ?? '—'}d` }
                    ].map(stat => (
                      <div key={stat.label} className="flex flex-col gap-1">
                        <span className="text-[9px] text-slate-500 uppercase font-black tracking-widest">{stat.label}</span>
                        <span className={`font-mono font-black text-lg ${stat.color || 'text-white'}`}>{stat.val}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-background/90 backdrop-blur-2xl z-[150] flex items-center justify-center p-4 md:p-8">
          <motion.div initial={{ opacity: 0, scale: 0.98, y: 20 }} animate={{ opacity: 1, scale: 1, y: 0 }} className="glass-card w-full max-w-[1200px] p-8 md:p-12 rounded-[3rem] border border-white/10 shadow-2xl relative max-h-[90vh] overflow-y-auto scrollbar-none">
            <div className="flex justify-between items-start mb-10">
               <div><h2 className="text-4xl font-black text-white tracking-tight mb-2">{editingConcept ? "Update Card" : "Initialize New Card"}</h2><p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px]">Neural Protocol: Concept Mapping</p></div>
               <button onClick={() => setShowModal(false)} className="p-3 rounded-full glass hover:bg-white/10 text-slate-400 transition-all border border-white/5"><X size={24} /></button>
            </div>
            <form onSubmit={handleSubmitConcept} className="space-y-10">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
                <div className="space-y-8">
                  <div className="space-y-3"><label className="text-[10px] font-black uppercase tracking-[0.3em] text-primary ml-1">Card Title (Knowledge Map Identity)</label><input type="text" autoFocus required placeholder="e.g. Asymptotic Notation" className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-6 py-5 text-white text-xl font-bold focus:ring-4 focus:ring-primary/10 outline-none transition-all placeholder:text-slate-800" value={newTitle} onChange={e => setNewTitle(e.target.value)} /></div>
                  
                  <div className="space-y-3">
                    <label className="text-[10px] font-black uppercase tracking-[0.3em] text-accent ml-1">Prerequisite (Optional Bridge)</label>
                    <select 
                      className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-6 py-4 text-white font-bold focus:ring-4 focus:ring-accent/10 outline-none transition-all appearance-none"
                      value={parentConceptId}
                      onChange={e => setParentConceptId(e.target.value)}
                    >
                      <option value="" className="bg-slate-900 text-slate-500">No Prerequisite (Root Concept)</option>
                      {concepts
                        .filter(c => !editingConcept || c.id !== editingConcept.id)
                        .map(c => (
                        <option key={c.id} value={c.id} className="bg-slate-900 text-white">{c.title}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-3"><label className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500 ml-1">Card Front (Synaptic Trigger)</label><input type="text" required placeholder="Input the question or prompt..." className="w-full bg-white/[0.02] border border-white/5 rounded-2xl px-6 py-4 text-slate-300 text-lg focus:ring-4 focus:ring-white/5 outline-none transition-all placeholder:text-slate-900" value={newFrontMsg} onChange={e => setNewFrontMsg(e.target.value)} /></div>
                  <div className="space-y-3"><div className="flex justify-between items-center ml-1"><label className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Card Back (Synaptic Payload)</label><span className="text-[8px] uppercase font-black text-slate-600 tracking-widest bg-white/5 px-2 py-1 rounded">Markdown Core</span></div><textarea required className="w-full bg-white/[0.03] border border-white/10 rounded-3xl px-6 py-6 text-slate-300 focus:ring-4 focus:ring-primary/5 outline-none h-64 resize-none font-medium text-lg leading-relaxed transition-all placeholder:text-slate-800" value={newBackMsg} onChange={e => setNewBackMsg(e.target.value)} placeholder="Describe the atomic facts using **bold**, `code`, or [links]..."></textarea></div>
                </div>
                <div className="space-y-6">
                   <div className="flex justify-between items-center px-1"><div className="flex items-center gap-3"><div className={`p-2 rounded-lg transition-all ${showCodeInput ? 'bg-primary/20 text-primary border border-primary/30' : 'bg-white/5 text-slate-600 border border-white/5'}`}><Code2 size={20} /></div><h3 className={`text-sm font-black uppercase tracking-widest ${showCodeInput ? 'text-white' : 'text-slate-600'}`}>Logic / Code Sandbox</h3></div><button type="button" onClick={() => setShowCodeInput(!showCodeInput)} className={`px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest transition-all ${showCodeInput ? 'bg-destructive/20 text-destructive border border-destructive/20' : 'bg-primary text-primary-foreground shadow-lg shadow-primary/20'}`}>{showCodeInput ? "Remove Logic" : "Inject Logic"}</button></div>
                   {showCodeInput ? (<div className="h-[430px] rounded-[2rem] overflow-hidden border border-white/10 shadow-inner animate-in zoom-in-95 duration-500"><CodeEditor code={codeSnippet} language={subject?.name?.toLowerCase().includes('c++') ? 'cpp' : 'javascript'} onChange={(val) => setCodeSnippet(val)} /></div>) : (<div className="h-[430px] rounded-[3rem] border-2 border-dashed border-white/5 flex flex-col items-center justify-center text-center p-10 group hover:border-white/10 transition-colors"><Code2 size={48} className="text-slate-700 mb-6 group-hover:scale-110 transition-transform duration-500" /><p className="text-[10px] font-black text-slate-600 uppercase tracking-[0.3em] mb-4">No Logic Injected</p><p className="text-xs text-slate-500 leading-relaxed max-w-[200px]">Optional: Add an executable code snippet to strengthen this concept during study sessions.</p></div>)}
                </div>
              </div>
              <div className="flex flex-col sm:flex-row gap-4 pt-6 border-t border-white/5"><button type="button" onClick={() => setShowModal(false)} className="flex-1 py-5 rounded-2xl glass hover:bg-white/10 transition-all font-black text-[11px] uppercase tracking-[0.3em] text-white border border-white/5">Abort Session</button><button type="submit" className="flex-[2] py-5 rounded-2xl bg-primary text-primary-foreground hover:opacity-90 transition-all font-black text-[11px] uppercase tracking-[0.3em] shadow-2xl shadow-primary/20 active:scale-95">{editingConcept ? "Synchronize Card" : "Initialize Card"}</button></div>
            </form>
          </motion.div>
        </div>
      )}

      {/* Neural Recap Modal */}
      {showRecapModal && (
        <div className="fixed inset-0 bg-background/95 backdrop-blur-3xl z-[200] flex items-center justify-center p-4 md:p-8">
           <motion.div initial={{ opacity: 0, scale: 0.95 }} animate={{ opacity: 1, scale: 1 }} className="glass-card w-full max-w-4xl p-10 rounded-[3rem] border border-white/10 shadow-3xl relative flex flex-col max-h-[90vh]">
              <div className="flex justify-between items-start mb-8 border-b border-white/5 pb-6">
                 <div className="flex items-center gap-4"><div className="p-3 bg-primary/20 rounded-2xl border border-primary/30"><Trophy className="text-primary" size={28} /></div><div><h2 className="text-3xl font-black text-white tracking-tighter">Neural Cheat Sheet</h2><p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest">AI-Synthesized Subject Summary</p></div></div>
                 <button onClick={() => setShowRecapModal(false)} className="p-3 rounded-xl hover:bg-white/5 text-slate-500 hover:text-white transition-all"><X size={24} /></button>
              </div>
              <div className="flex-grow overflow-y-auto pr-6 scrollbar-thin scrollbar-thumb-white/10">
                 {loadingRecap ? (<div className="h-full flex flex-col items-center justify-center gap-6 py-20"><Loader2 className="animate-spin text-primary" size={48} /><p className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-500">Synthesizing Core Concepts...</p></div>) : (<div className="prose prose-invert prose-indigo max-w-none"><ReactMarkdown>{recapMarkdown}</ReactMarkdown></div>)}
              </div>
              <div className="mt-8 pt-8 border-t border-white/5"><button onClick={() => { setShowRecapModal(false); startCramMode(); }} className="w-full py-5 bg-amber-500 text-black rounded-2xl font-black text-xs uppercase tracking-[0.3em] shadow-2xl shadow-amber-500/20 hover:scale-[1.02] transition-all">Enter Exam Protocol Now</button></div>
           </motion.div>
        </div>
      )}
    </div>
  );
};

export default SubjectDetail;
