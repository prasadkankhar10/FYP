import React, { useState, useEffect, useMemo } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Plus, BookOpen, Loader2, ArrowRight, Trash2, Search, Filter, LayoutGrid, Archive, GraduationCap, Microscope, Languages, Code, Play, Zap } from 'lucide-react';
import api, { showToast } from '../api';

const SUBJECT_TEMPLATES = [
  { id: 'general', name: 'General Study', icon: <GraduationCap size={18} />, desc: 'Standard spaced repetition for any topic.' },
  { id: 'stem', name: 'STEM / Math', icon: <Microscope size={18} />, desc: 'Optimized for formulas, LaTeX, and logical concepts.' },
  { id: 'languages', name: 'Language Learning', icon: <Languages size={18} />, desc: 'Focus on vocabulary, phonetics, and grammar.' },
  { id: 'cs', name: 'Computer Science', icon: <Code size={18} />, desc: 'Syntax highlighting and algorithmic logic mapping.' }
];

const Subjects = () => {
  const [subjects, setSubjects] = useState([]);
  const [subjectStats, setSubjectStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState('all');
  
  const [newSubjectName, setNewSubjectName] = useState('');
  const [newSubjectDesc, setNewSubjectDesc] = useState('');
  const [selectedTemplate, setSelectedTemplate] = useState('general');

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/subjects/');
      const subs = res.data;
      setSubjects(subs);
      
      const stats = {};
      await Promise.all(
        subs.map(async (sub) => {
          try {
            const cRes = await api.get(`/concepts/?subject_id=${sub.id}`);
            const concepts = cRes.data;
            
            // Fetch scheduling for each to get avg R
            let totalR = 0;
            let countWithR = 0;
            
            for (const c of concepts) {
              try {
                const sRes = await api.get(`/schedule/${c.id}`);
                if (sRes.data.retrievability != null) {
                  totalR += sRes.data.retrievability;
                  countWithR++;
                }
              } catch {}
            }
            
            stats[sub.id] = {
              count: concepts.length,
              avgR: countWithR > 0 ? (totalR / countWithR) : 1.0
            };
          } catch { stats[sub.id] = { count: 0, avgR: 1.0 }; }
        })
      );
      setSubjectStats(stats);
    } catch (err) {
      showToast("Failed to load subjects", "error");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const filteredSubjects = useMemo(() => {
    return subjects.filter(s => 
      s.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (s.description && s.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );
  }, [subjects, searchTerm]);

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    if (!newSubjectName.trim()) return;
    try {
      await api.post('/subjects/', { 
        name: newSubjectName, 
        description: `${SUBJECT_TEMPLATES.find(t => t.id === selectedTemplate).name}: ${newSubjectDesc}` 
      });
      setShowModal(false);
      setNewSubjectName('');
      setNewSubjectDesc('');
      showToast("Subject created successfully!", "success");
      fetchSubjects();
    } catch (err) {
      showToast("Failed to create subject", "error");
    }
  };

  const handleDeleteSubject = async (e, subjectId) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm("Delete this subject and ALL its concepts?")) return;
    try {
      await api.delete(`/subjects/${subjectId}`);
      showToast("Subject deleted", "info");
      fetchSubjects();
    } catch (err) {
      showToast("Delete failed", "error");
    }
  };

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-primary" size={48} /></div>;
  }

  return (
    <div className="p-8 max-w-7xl w-full mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-12">
        <div>
          <h1 className="text-4xl font-bold tracking-tight mb-2">Knowledge Base</h1>
          <p className="text-muted-foreground">Manage and organize your learning branches.</p>
        </div>
        <button 
          onClick={() => setShowModal(true)}
          className="hidden md:flex items-center gap-2 bg-primary px-6 py-3 rounded-2xl text-primary-foreground font-bold hover:opacity-90 transition-all shadow-lg shadow-primary/20 hover:scale-105 active:scale-95"
        >
          <Plus size={20} /> Create New Subject
        </button>
      </div>

      {/* Mobile FAB */}
      <button 
        onClick={() => setShowModal(true)}
        className="md:hidden fixed bottom-28 right-6 z-40 w-14 h-14 bg-primary text-primary-foreground rounded-full flex items-center justify-center shadow-[0_0_20px_rgba(139,92,246,0.3)] hover:scale-105 active:scale-95 transition-all"
      >
        <Plus size={28} />
      </button>

      <div className="flex flex-col md:flex-row gap-4 mb-8">
        <div className="relative flex-1">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-muted-foreground" size={18} />
          <input 
            type="text"
            placeholder="Search subjects..."
            className="w-full bg-white/5 border border-white/10 rounded-2xl pl-12 pr-4 py-3.5 focus:ring-2 focus:ring-primary outline-none transition-all"
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
          />
        </div>
        <div className="flex gap-2">
          <button className="flex items-center gap-2 px-4 py-3.5 rounded-2xl glass hover:bg-white/10 transition-colors text-sm font-medium">
            <Filter size={18} /> Filters
          </button>
          <button className="flex items-center gap-2 px-4 py-3.5 rounded-2xl bg-white/10 text-white transition-colors text-sm font-medium">
            <LayoutGrid size={18} />
          </button>
        </div>
      </div>

      {filteredSubjects.length === 0 ? (
        <div className="glass-card p-20 rounded-[2rem] text-center border-dashed border-2">
          <BookOpen size={64} className="mx-auto text-muted-foreground mb-6 opacity-20" />
          <h3 className="text-2xl font-bold mb-2">No subjects found</h3>
          <p className="text-muted-foreground max-w-md mx-auto">
            Try adjusting your search or create a new subject to begin your learning journey.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-8">
          {filteredSubjects.map(sub => {
            const stats = subjectStats[sub.id] || { count: 0, avgR: 1.0 };
            return (
              <div key={sub.id} className="group">
                <div className="glass-card p-8 rounded-[2rem] h-full flex flex-col relative overflow-hidden transition-all hover:-translate-y-2 hover:shadow-2xl border border-white/5 hover:border-primary/30">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-16 translate-x-16 blur-3xl group-hover:bg-primary/20 transition-all pointer-events-none"></div>
                  
                  <div className="flex justify-between items-start relative z-10 mb-6">
                    <div className="p-3 bg-white/5 rounded-2xl text-primary">
                      <GraduationCap size={24} />
                    </div>
                    <div className="flex items-center gap-1 opacity-80 group-hover:opacity-100 transition-all">
                      <button 
                        onClick={(e) => { e.preventDefault(); e.stopPropagation(); }}
                        className="p-2 hover:bg-white/10 rounded-xl text-muted-foreground hover:text-white"
                        title="Archive"
                      >
                        <Archive size={18} />
                      </button>
                      <button 
                        onClick={(e) => handleDeleteSubject(e, sub.id)}
                        className="p-2 hover:bg-destructive/10 rounded-xl text-muted-foreground hover:text-destructive"
                        title="Delete"
                      >
                        <Trash2 size={18} />
                      </button>
                    </div>
                  </div>

                  <Link to={`/subjects/${sub.id}`}>
                    <h3 className="text-2xl font-bold mb-2 group-hover:text-primary transition-colors">{sub.name}</h3>
                  </Link>
                  <p className="text-muted-foreground text-xs line-clamp-2 mb-6 flex-1 leading-relaxed">{sub.description}</p>
                  
                  <div className="space-y-4 relative z-10">
                    <div className="flex justify-between items-center text-xs">
                      <span className="text-muted-foreground">Retention Strength</span>
                      <span className={`font-mono font-bold ${stats.avgR >= 0.85 ? 'text-success' : stats.avgR >= 0.5 ? 'text-warning' : 'text-destructive'}`}>
                        {(stats.avgR * 100).toFixed(0)}%
                      </span>
                    </div>
                    <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-primary transition-all duration-1000" 
                        style={{ width: `${stats.avgR * 100}%` }}
                      ></div>
                    </div>

                    <div className="flex items-center justify-between pt-3 border-t border-white/5 gap-2">
                      <Link 
                        to={`/study?subject_id=${sub.id}`}
                        className="flex-1 py-2 px-3 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-xl text-[10px] font-black uppercase tracking-wider shadow-lg shadow-indigo-500/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-1.5"
                      >
                        <Play size={12} className="fill-current" /> Study Subject
                      </Link>
                      <Link
                        to={`/subjects/${sub.id}`}
                        className="py-2 px-3 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-xl text-[10px] font-bold uppercase tracking-wider border border-white/5 transition-all flex items-center gap-1"
                      >
                        Cards ({stats.count}) <ArrowRight size={12} />
                      </Link>
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-background/80 backdrop-blur-xl z-[100] flex items-center justify-center p-6">
          <div className="glass-card w-full max-w-2xl p-10 rounded-[2.5rem] border shadow-2xl animate-in zoom-in-95 duration-200">
            <h2 className="text-3xl font-bold mb-2">Create New Subject</h2>
            <p className="text-muted-foreground mb-8">Choose a template to get started with optimized defaults.</p>
            
            <form onSubmit={handleCreateSubject} className="space-y-8">
              <div className="grid grid-cols-2 gap-4">
                {SUBJECT_TEMPLATES.map(t => (
                  <button
                    key={t.id}
                    type="button"
                    onClick={() => setSelectedTemplate(t.id)}
                    className={`p-4 rounded-2xl border text-left transition-all ${selectedTemplate === t.id ? 'bg-primary/10 border-primary ring-1 ring-primary' : 'bg-white/5 border-white/5 hover:bg-white/10'}`}
                  >
                    <div className={`p-2 rounded-xl mb-3 w-fit ${selectedTemplate === t.id ? 'bg-primary text-white' : 'bg-white/5 text-slate-400'}`}>
                      {t.icon}
                    </div>
                    <div className="font-bold text-sm mb-1">{t.name}</div>
                    <div className="text-xs text-muted-foreground leading-relaxed">{t.desc}</div>
                  </button>
                ))}
              </div>

              <div className="space-y-4">
                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-300 ml-1">Subject Name</label>
                  <input 
                    type="text" autoFocus required
                    placeholder="e.g. Molecular Biology"
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white focus:ring-2 focus:ring-primary outline-none transition-all"
                    value={newSubjectName} onChange={e => setNewSubjectName(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-sm font-bold text-slate-300 ml-1">Research Focus (Optional)</label>
                  <textarea 
                    className="w-full bg-white/5 border border-white/10 rounded-2xl px-5 py-4 text-white focus:ring-2 focus:ring-primary outline-none transition-all resize-none"
                    rows="3"
                    placeholder="Define what you want to achieve with this subject..."
                    value={newSubjectDesc} onChange={e => setNewSubjectDesc(e.target.value)}
                  ></textarea>
                </div>
              </div>

              <div className="flex gap-4 pt-2">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-4 rounded-2xl glass hover:bg-white/10 transition-colors font-bold">
                  Cancel
                </button>
                <button type="submit" className="flex-1 py-4 rounded-2xl bg-primary text-primary-foreground hover:opacity-90 transition-all font-bold shadow-lg shadow-primary/20">
                  Create Subject
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default Subjects;
