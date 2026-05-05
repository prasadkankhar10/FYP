import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { Plus, BrainCircuit, Loader2, ArrowLeft, Trash2, Edit2 } from 'lucide-react';
import api from '../api';

const SubjectDetail = () => {
  const { id } = useParams();
  const [subject, setSubject] = useState(null);
  const [concepts, setConcepts] = useState([]);
  const [schedMap, setSchedMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  
  const [newTitle, setNewTitle] = useState('');
  const [newFrontMsg, setNewFrontMsg] = useState('');
  const [newBackMsg, setNewBackMsg] = useState('');
  const [editingConcept, setEditingConcept] = useState(null);

  const fetchData = async () => {
    try {
      const subRes = await api.get('/subjects/');
      const currentSub = subRes.data.find(s => s.id === parseInt(id));
      if (currentSub) setSubject(currentSub);

      const conceptRes = await api.get(`/concepts/?subject_id=${id}`);
      setConcepts(conceptRes.data);

      // Fetch scheduling data for each concept (for S/D/R display)
      const schedData = {};
      await Promise.all(
        conceptRes.data.map(async (c) => {
          try {
            const sRes = await api.get(`/schedule/${c.id}`);
            schedData[c.id] = sRes.data;
          } catch { /* no sched data */ }
        })
      );
      setSchedMap(schedData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [id]);

  const handleSubmitConcept = async (e) => {
    e.preventDefault();
    try {
      if (editingConcept) {
        await api.put(`/concepts/${editingConcept.id}`, {
          title: newTitle,
          content: newBackMsg
        });
      } else {
        await api.post('/concepts/', {
          subject_id: parseInt(id),
          title: newTitle,
          content: newBackMsg,
          parent_concept_id: null
        });
      }
      setShowModal(false);
      setEditingConcept(null);
      setNewTitle('');
      setNewBackMsg('');
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const openAddModal = () => {
    setEditingConcept(null);
    setNewTitle('');
    setNewBackMsg('');
    setShowModal(true);
  };

  const openEditModal = (concept) => {
    setEditingConcept(concept);
    setNewTitle(concept.title);
    setNewBackMsg(concept.content);
    setShowModal(true);
  };

  const handleDelete = async (conceptId) => {
    if (!window.confirm("Delete this concept?")) return;
    try {
      await api.delete(`/concepts/${conceptId}`);
      fetchData();
    } catch (err) {
      console.error(err);
    }
  };

  const getRetColor = (r) => {
    if (r >= 0.85) return 'text-green-400';
    if (r >= 0.5) return 'text-amber-400';
    return 'text-red-400';
  };

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-purple-400" size={48} /></div>;
  }

  if (!subject) {
    return <div className="p-8">Subject not found.</div>;
  }

  return (
    <div className="p-8 max-w-6xl w-full">
      <Link to="/subjects" className="text-slate-400 hover:text-white flex items-center gap-2 w-fit mb-6 transition-colors">
        <ArrowLeft size={18} /> Back to Subjects
      </Link>
      
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-4xl font-bold">{subject.name}</h1>
          <p className="text-slate-400 mt-2 text-lg">{subject.description}</p>
        </div>
        <button 
          onClick={openAddModal}
          className="flex items-center gap-2 bg-gradient-to-r from-blue-500 to-purple-600 px-5 py-2.5 rounded-xl text-white hover:opacity-90 transition-opacity"
        >
          <Plus size={20} /> Add Concept
        </button>
      </div>

      {concepts.length === 0 ? (
        <div className="glass p-12 rounded-3xl text-center border-dashed border-2 border-white/20">
          <BrainCircuit size={48} className="mx-auto text-slate-500 mb-4" />
          <h3 className="text-xl font-medium text-slate-300">Explore new knowledge</h3>
          <p className="text-slate-500 mt-2">Add concepts to start building your flashcards.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {concepts.map(concept => {
            const sched = schedMap[concept.id];
            return (
              <div key={concept.id} className="glass p-5 rounded-xl flex flex-col group">
                <div className="flex justify-between items-start">
                  <div className="flex flex-col flex-1 min-w-0">
                    <h4 className="text-xl font-semibold text-white truncate">{concept.title}</h4>
                    <div className="flex items-center gap-3 text-sm mt-1 flex-wrap">
                      <span className="bg-purple-600/30 text-purple-300 px-2 py-0.5 rounded font-bold uppercase text-xs">{concept.algorithm || 'NEW'}</span>
                      <span className="text-slate-400">Next: <span className="text-slate-300 font-medium">{concept.next_review_date ? new Date(concept.next_review_date + 'Z').toLocaleDateString() : 'Now'}</span></span>
                    </div>
                  </div>
                  <div className="flex gap-2 opacity-0 group-hover:opacity-100 transition-all ml-2">
                    <button 
                      onClick={() => openEditModal(concept)}
                      className="text-slate-500 hover:text-blue-400 p-2 bg-white/5 rounded-lg hover:bg-blue-400/10"
                    >
                      <Edit2 size={18} />
                    </button>
                    <button 
                      onClick={() => handleDelete(concept.id)}
                      className="text-slate-500 hover:text-red-400 p-2 bg-white/5 rounded-lg hover:bg-red-400/10"
                    >
                      <Trash2 size={18} />
                    </button>
                  </div>
                </div>

                {/* S / D / R metrics */}
                {sched && (
                  <div className="flex gap-4 mt-3 pt-3 border-t border-white/5 text-xs">
                    <div className="flex flex-col items-center">
                      <span className="text-slate-500 uppercase tracking-wider">Stability</span>
                      <span className="text-white font-mono font-bold text-sm">{sched.stability?.toFixed(1) ?? '—'}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-slate-500 uppercase tracking-wider">Difficulty</span>
                      <span className="text-white font-mono font-bold text-sm">{sched.difficulty_fsrs?.toFixed(1) ?? '—'}</span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-slate-500 uppercase tracking-wider">Retriev.</span>
                      <span className={`font-mono font-bold text-sm ${getRetColor(sched.retrievability ?? 1)}`}>
                        {sched.retrievability != null ? (sched.retrievability * 100).toFixed(0) + '%' : '—'}
                      </span>
                    </div>
                    <div className="flex flex-col items-center">
                      <span className="text-slate-500 uppercase tracking-wider">Interval</span>
                      <span className="text-white font-mono font-bold text-sm">{sched.interval_days ?? '—'}d</span>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass w-full max-w-lg p-8 rounded-3xl border border-white/20">
            <h2 className="text-2xl font-bold mb-6">{editingConcept ? "Edit Concept" : "Add New Concept"}</h2>
            <form onSubmit={handleSubmitConcept} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Concept Title (Front)</label>
                <input 
                  type="text" autoFocus required
                  className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 mb-4"
                  value={newTitle} onChange={e => setNewTitle(e.target.value)}
                  placeholder="e.g. Mitosis"
                />
                <label className="block text-sm font-medium text-slate-300 mb-2">Detailed Answer (Back)</label>
                <textarea 
                  required
                  className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-purple-500 h-32 resize-none"
                  value={newBackMsg} onChange={e => setNewBackMsg(e.target.value)}
                  placeholder="e.g. Process of cell duplication..."
                ></textarea>
              </div>
              <div className="flex gap-4 mt-6">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-3 rounded-xl border border-white/10 hover:bg-white/5 transition-colors">
                  Cancel
                </button>
                <button type="submit" className="flex-1 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 transition-colors">
                  {editingConcept ? "Update Concept" : "Create Concept"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default SubjectDetail;
