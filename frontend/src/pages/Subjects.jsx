import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Plus, BookOpen, Loader2, ArrowRight, Trash2 } from 'lucide-react';
import api from '../api';

const Subjects = () => {
  const [subjects, setSubjects] = useState([]);
  const [conceptCounts, setConceptCounts] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [newSubjectName, setNewSubjectName] = useState('');
  const [newSubjectDesc, setNewSubjectDesc] = useState('');

  const fetchSubjects = async () => {
    try {
      const res = await api.get('/subjects/');
      setSubjects(res.data);
      // Fetch concept counts per subject
      const counts = {};
      await Promise.all(
        res.data.map(async (sub) => {
          try {
            const cRes = await api.get(`/concepts/?subject_id=${sub.id}`);
            counts[sub.id] = cRes.data.length;
          } catch { counts[sub.id] = 0; }
        })
      );
      setConceptCounts(counts);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubjects();
  }, []);

  const handleCreateSubject = async (e) => {
    e.preventDefault();
    if (!newSubjectName.trim()) return;
    try {
      await api.post('/subjects/', { name: newSubjectName, description: newSubjectDesc });
      setShowModal(false);
      setNewSubjectName('');
      setNewSubjectDesc('');
      fetchSubjects();
    } catch (err) {
      console.error(err);
    }
  };

  const handleDeleteSubject = async (e, subjectId) => {
    e.preventDefault();
    e.stopPropagation();
    if (!window.confirm("Delete this subject and ALL its concepts? This cannot be undone.")) return;
    try {
      await api.delete(`/subjects/${subjectId}`);
      fetchSubjects();
    } catch (err) {
      console.error(err);
      alert("Failed to delete subject.");
    }
  };

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-purple-400" size={48} /></div>;
  }

  return (
    <div className="p-8 max-w-6xl w-full">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-4xl font-bold">Your Subjects</h1>
        <button 
          onClick={() => setShowModal(true)}
          className="flex items-center gap-2 bg-gradient-to-r from-purple-500 to-pink-600 px-5 py-2.5 rounded-xl text-white hover:opacity-90 transition-opacity"
        >
          <Plus size={20} /> New Subject
        </button>
      </div>

      {subjects.length === 0 ? (
        <div className="glass p-12 rounded-3xl text-center border-dashed border-2 border-white/20">
          <BookOpen size={48} className="mx-auto text-slate-500 mb-4" />
          <h3 className="text-xl font-medium text-slate-300">No subjects found</h3>
          <p className="text-slate-500 mt-2">Create your first subject to start organizing your concepts.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {subjects.map(sub => (
            <Link to={`/subjects/${sub.id}`} key={sub.id}>
              <div className="glass p-6 rounded-2xl h-full flex flex-col group hover:border-purple-500/50 transition-colors cursor-pointer relative overflow-hidden">
                <div className="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-pink-600/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
                <div className="flex justify-between items-start relative z-10">
                  <h3 className="text-2xl font-bold text-white mb-2 truncate flex-1">{sub.name}</h3>
                  <button
                    onClick={(e) => handleDeleteSubject(e, sub.id)}
                    className="text-slate-600 hover:text-red-400 p-1.5 rounded-lg hover:bg-red-400/10 opacity-0 group-hover:opacity-100 transition-all ml-2"
                    title="Delete subject"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
                <p className="text-slate-400 relative z-10 flex-1 line-clamp-3">{sub.description || 'No description provided.'}</p>
                <div className="mt-4 flex items-center justify-between relative z-10">
                  <span className="text-sm text-slate-500">{conceptCounts[sub.id] || 0} concepts</span>
                  <div className="flex items-center gap-2 text-purple-400 font-medium group-hover:translate-x-1 transition-transform">
                    View <ArrowRight size={18} />
                  </div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      {showModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="glass w-full max-w-lg p-8 rounded-3xl border border-white/20">
            <h2 className="text-2xl font-bold mb-6">Create New Subject</h2>
            <form onSubmit={handleCreateSubject} className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Subject Name</label>
                <input 
                  type="text" autoFocus required
                  className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-purple-500"
                  value={newSubjectName} onChange={e => setNewSubjectName(e.target.value)}
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">Description (Optional)</label>
                <textarea 
                  className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-purple-500"
                  rows="3"
                  value={newSubjectDesc} onChange={e => setNewSubjectDesc(e.target.value)}
                ></textarea>
              </div>
              <div className="flex gap-4 mt-4">
                <button type="button" onClick={() => setShowModal(false)} className="flex-1 py-3 rounded-xl border border-white/10 hover:bg-white/5 transition-colors">
                  Cancel
                </button>
                <button type="submit" className="flex-1 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 transition-colors">
                  Create
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
