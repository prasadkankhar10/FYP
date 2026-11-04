import React, { useState, useContext, useEffect } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Bot, Save, Loader2, Sparkles, BookOpen, Code2, Zap, Terminal, Cpu, Database, Network, Layout, Search, ArrowRight, X, Trash2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api, { showToast } from '../api';

const AiTutor = () => {
  const { user } = useContext(AuthContext);
  const [bio, setBio] = useState('');
  const [savingBio, setSavingBio] = useState(false);
  
  const [advice, setAdvice] = useState('');
  const [loadingAdvice, setLoadingAdvice] = useState(false);

  const [pdfText, setPdfText] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [generatingC, setGeneratingC] = useState(false);
  
  const [previewCards, setPreviewCards] = useState([]);
  const [savingCards, setSavingCards] = useState(false);
  const [optimizingGraph, setOptimizingGraph] = useState(false);

  // New Code-Specific State
  const [codeToAnalyze, setCodeToAnalyze] = useState('');
  const [codeAnalysis, setCodeAnalysis] = useState(null);
  const [analyzingCode, setAnalyingCode] = useState(false);
  
  useEffect(() => {
    const loadData = async () => {
      try {
        const uRes = await api.get('/auth/me');
        if (uRes.data.bio) setBio(uRes.data.bio);
        const subRes = await api.get('/subjects/');
        setSubjects(subRes.data);
      } catch (e) {
        console.error(e);
      }
    };
    loadData();
  }, []);

  const handleSaveBio = async () => {
    setSavingBio(true);
    try {
      await api.put('/auth/me', { bio });
      showToast("Profile synchronized", "success");
    } catch (err) {
      showToast("Failed to save profile", "error");
    } finally {
      setSavingBio(false);
    }
  };

  const fetchAdvice = async () => {
    setLoadingAdvice(true);
    setAdvice('');
    try {
      const res = await api.get('/ai/advisor');
      setAdvice(res.data.advice_markdown);
    } catch (err) {
      showToast("Tutor unavailable", "error");
    } finally {
      setLoadingAdvice(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    if (!selectedSubject || !pdfText) {
      showToast("Context required: select subject and provide text", "info");
      return;
    }
    setGeneratingC(true);
    try {
      const res = await api.post('/ai/generate-flashcards', {
        subject_id: parseInt(selectedSubject),
        source_text: pdfText
      });
      setPreviewCards(res.data.cards);
      showToast("Flashcards synthesized", "success");
    } catch (err) {
      showToast("Generation failed", "error");
    } finally {
      setGeneratingC(false);
    }
  };

  const handleSaveFlashcards = async () => {
    setSavingCards(true);
    try {
      const res = await api.post('/ai/save-flashcards', {
        subject_id: parseInt(selectedSubject),
        cards: previewCards
      });
      showToast(`Saved ${res.data.concepts_created} cards to Knowledge Base`, "success");
      setPreviewCards([]);
      setPdfText('');
    } catch (err) {
      showToast("Failed to commit cards", "error");
    } finally {
      setSavingCards(false);
    }
  };

  const handleAnalyzeCode = async () => {
    if (!codeToAnalyze.trim()) return;
    setAnalyingCode(true);
    try {
      const res = await api.post('/ai/evaluate-answer', {
        concept_id: -1, // Special ID for ad-hoc analysis
        typed_answer: `ANALYZE THIS CODE FOR BIG-O COMPLEXITY AND SUGGEST REFACTOR:\n\n\`\`\`\n${codeToAnalyze}\n\`\`\``
      });
      setCodeAnalysis(res.data.feedback_markdown);
      showToast("Logic analysis complete", "success");
    } catch (err) {
      showToast("Code analysis failed", "error");
    } finally {
      setAnalyingCode(false);
    }
  };

  const handleConnectGraph = async () => {
    setOptimizingGraph(true);
    showToast("AI is scanning concepts for logical prerequisites...", "info");
    try {
      const res = await api.post('/ai/connect-concepts');
      showToast(`Neural Optimization Complete: ${res.data.connections_made} new synapses mapped`, "success");
    } catch (err) {
      showToast("Optimization failed. The logic engine might be busy.", "error");
    } finally {
      setOptimizingGraph(false);
    }
  };

  return (
    <div className="p-4 md:p-12 max-w-[1600px] w-full mx-auto animate-in fade-in duration-700">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-16">
        <div>
          <div className="flex items-center gap-4 mb-2">
            <div className="p-3 bg-primary/20 rounded-2xl border border-primary/30">
               <Bot className="text-primary" size={32} />
            </div>
            <h1 className="text-4xl font-black tracking-tighter text-white">Socratic AI Tutor</h1>
          </div>
          <p className="text-slate-500 font-bold uppercase tracking-[0.2em] text-[10px] ml-[70px]">Advanced Pedagogical Logic Engine</p>
        </div>
        
        <div className="flex gap-3 w-full md:w-auto">
           <button 
            onClick={handleConnectGraph} 
            disabled={optimizingGraph}
            className="flex-1 md:flex-none flex items-center justify-center gap-2 glass px-6 py-3 rounded-2xl text-[10px] font-black uppercase tracking-widest hover:bg-white/5 transition-all text-white border border-white/5 disabled:opacity-50"
           >
              {optimizingGraph ? <Loader2 size={14} className="animate-spin text-secondary" /> : <Network size={14} className="text-secondary" />}
              {optimizingGraph ? 'Optimizing...' : 'Re-Optimize Graph'}
           </button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left: Input Pipeline */}
        <div className="lg:col-span-4 space-y-8 text-white">
          <div className="glass-card p-8 rounded-[2.5rem] border border-white/5 relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full blur-3xl group-hover:bg-primary/10 transition-all"></div>
            <h2 className="text-xl font-black mb-1 flex items-center gap-3 relative z-10 text-white"><Database size={20} className="text-primary" /> Cognitive Profile</h2>
            <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-6 relative z-10">Tailoring logic to your background</p>
            
            <textarea
              className="w-full bg-white/[0.03] border border-white/10 rounded-2xl px-5 py-4 text-white focus:ring-4 focus:ring-primary/10 outline-none h-32 resize-none mb-6 text-sm transition-all"
              placeholder="e.g. Master's in Data Science, focusing on Transformer architectures. Struggling with Attention mechanism math."
              value={bio}
              onChange={(e) => setBio(e.target.value)}
            ></textarea>
            
            <button 
              onClick={handleSaveBio}
              disabled={savingBio}
              className="w-full py-4 bg-white/5 hover:bg-white/10 rounded-2xl transition-all flex items-center justify-center gap-2 font-black text-[10px] uppercase tracking-[0.2em] border border-white/5 text-white"
            >
              {savingBio ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
              Sync Profile
            </button>
          </div>

          <div className="glass-card p-8 rounded-[2.5rem] border border-blue-500/20 bg-blue-500/[0.02] relative overflow-hidden group">
             <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/10 blur-[80px] rounded-full group-hover:bg-blue-500/20 transition-all"></div>
             
             <h2 className="text-xl font-black mb-1 text-blue-400 flex items-center gap-3 relative z-10">
                <Sparkles size={20} /> Neural Distillation
             </h2>
             <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mb-6 relative z-10">Synthesize cards from raw data</p>
             
             <select 
               className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white mb-4 focus:ring-2 focus:ring-blue-500 text-xs font-bold"
               value={selectedSubject}
               onChange={(e) => setSelectedSubject(e.target.value)}
             >
                <option value="">Select Domain...</option>
                {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
             </select>

             <textarea
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 h-40 resize-none mb-4 text-xs leading-relaxed transition-all"
              placeholder="Paste raw research, documentation, or lecture transcripts..."
              value={pdfText}
              onChange={(e) => setPdfText(e.target.value)}
              disabled={previewCards.length > 0}
             ></textarea>

             {previewCards.length > 0 ? (
               <div className="space-y-4 animate-in zoom-in-95 duration-500">
                 <div className="bg-black/60 rounded-xl p-4 max-h-48 overflow-y-auto border border-white/5 scrollbar-thin">
                   {previewCards.map((card, idx) => (
                     <div key={idx} className="mb-4 border-b border-white/5 pb-3 last:border-0">
                       <p className="font-bold text-white text-[11px] mb-1">CARD: {card.title}</p>
                       <p className="text-slate-500 text-[10px] leading-relaxed italic">"{card.content}"</p>
                     </div>
                   ))}
                 </div>
                 <div className="flex gap-3">
                   <button onClick={() => setPreviewCards([])} disabled={savingCards} className="flex-1 py-3 rounded-xl glass hover:bg-destructive/10 hover:text-destructive transition-all font-black text-[9px] uppercase tracking-widest border border-white/5 text-white">Discard</button>
                   <button onClick={handleSaveFlashcards} disabled={savingCards} className="flex-[2] py-3 rounded-xl bg-success text-success-foreground transition-all font-black text-[9px] uppercase tracking-widest shadow-lg shadow-success/20 flex justify-center items-center gap-2">{savingCards ? <Loader2 className="animate-spin" size={14} /> : <Zap size={14} fill="currentColor" />} Commit to Graph</button>
                 </div>
               </div>
             ) : (
               <button 
                 onClick={handleGenerateFlashcards}
                 disabled={generatingC || !selectedSubject || !pdfText}
                 className="w-full py-4 rounded-xl bg-blue-600 text-white transition-all font-black text-[10px] uppercase tracking-[0.2em] disabled:opacity-50 flex items-center justify-center gap-2 shadow-xl shadow-blue-600/20"
               >
                 {generatingC ? <Loader2 className="animate-spin" size={18} /> : <Cpu size={18} />}
                 Begin Distillation
               </button>
             )}
          </div>
        </div>

        {/* Right: Advanced DX Section */}
        <div className="lg:col-span-8 space-y-8 text-white">
          {/* Developer Intelligence Section */}
          <div className="glass-card p-10 rounded-[3rem] border border-purple-500/20 bg-purple-500/[0.01] relative overflow-hidden group">
            <div className="absolute top-0 right-0 w-96 h-96 bg-purple-500/5 blur-[120px] rounded-full pointer-events-none"></div>
            <div className="flex justify-between items-center mb-8 relative z-10">
              <div>
                <h2 className="text-2xl font-black tracking-tight flex items-center gap-3 text-white"><Code2 className="text-purple-400" /> Algorithmic Logic Analyzer</h2>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Optimization, Big-O Complexity & Refactoring</p>
              </div>
              <button 
                onClick={handleAnalyzeCode}
                disabled={analyzingCode || !codeToAnalyze}
                className="bg-purple-600 text-white px-8 py-3 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] shadow-xl shadow-purple-600/20 transition-all hover:scale-105 active:scale-95 disabled:opacity-50 flex items-center gap-2"
              >
                {analyzingCode ? <Loader2 className="animate-spin" size={16} /> : <Zap size={16} fill="currentColor" />}
                Analyze Logic
              </button>
            </div>
            
            <div className="grid grid-cols-1 xl:grid-cols-2 gap-8 relative z-10">
              <div className="space-y-4">
                <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg w-fit border border-white/5">
                   <Terminal size={12} className="text-slate-500" />
                   <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Input Source Code</span>
                </div>
                <textarea
                  className="w-full bg-black/40 border border-white/10 rounded-3xl p-6 text-white focus:ring-4 focus:ring-purple-500/10 outline-none h-[400px] font-mono text-xs leading-relaxed resize-none transition-all placeholder:text-slate-800"
                  placeholder="Paste your function or algorithm here to receive deep architectural feedback..."
                  value={codeToAnalyze}
                  onChange={(e) => setCodeToAnalyze(e.target.value)}
                ></textarea>
              </div>

              <div className="flex flex-col h-[400px]">
                <div className="flex items-center gap-2 px-3 py-1 bg-white/5 rounded-lg w-fit border border-white/5 mb-4">
                   <Cpu size={12} className="text-purple-400" />
                   <span className="text-[9px] font-black uppercase tracking-widest text-slate-400">Neural Response</span>
                </div>
                <div className="flex-1 bg-white/[0.02] border border-white/5 rounded-3xl p-8 overflow-y-auto scrollbar-thin text-white">
                  {codeAnalysis ? (
                    <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed font-sans">
                       <ReactMarkdown>{codeAnalysis}</ReactMarkdown>
                    </div>
                  ) : (
                    <div className="h-full flex flex-col items-center justify-center text-slate-600 text-center space-y-6">
                       <div className="p-8 bg-white/5 rounded-full border border-white/5 animate-pulse">
                          <Bot size={48} className="opacity-30" />
                       </div>
                       <p className="text-[10px] font-bold uppercase tracking-widest max-w-[200px]">Logic engine idle. Awaiting algorithmic input.</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Tutor Advice / Standard Section */}
          <div className="glass-card p-10 rounded-[3rem] border border-white/5 flex flex-col group">
            <div className="flex justify-between items-center mb-8 border-b border-white/5 pb-6">
              <div>
                <h2 className="text-2xl font-black tracking-tight flex items-center gap-3 text-white"><Layout className="text-primary" /> Curated Curriculum</h2>
                <p className="text-[10px] text-slate-500 font-bold uppercase tracking-widest mt-1">Generated based on your Cognitive Profile</p>
              </div>
              <button 
                onClick={fetchAdvice}
                disabled={loadingAdvice}
                className="bg-primary text-primary-foreground px-8 py-3 rounded-2xl font-black text-[10px] uppercase tracking-[0.2em] shadow-xl shadow-primary/20 transition-all hover:scale-105 disabled:opacity-50 flex items-center gap-2"
              >
                {loadingAdvice ? <Loader2 className="animate-spin" size={16} /> : <Search size={16} />}
                Generate Path
              </button>
            </div>
            
            <div className="flex-grow bg-white/[0.01] rounded-3xl p-8 overflow-y-auto min-h-[300px] text-white">
              {advice ? (
                <div className="prose prose-invert prose-indigo max-w-none text-slate-300 leading-relaxed">
                   <ReactMarkdown>{advice}</ReactMarkdown>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-600 text-center space-y-4">
                   <BookOpen size={48} className="opacity-20" />
                   <p className="text-[10px] font-bold uppercase tracking-widest">No active path detected. Ask the tutor to manifest one.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AiTutor;
