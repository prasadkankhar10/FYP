import React, { useContext, useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import api from './api';
import { Home, BookOpen, BrainCircuit, BarChart3, Settings, LogOut, Loader2, Library, Bot, Network, AlertTriangle, TrendingUp } from 'lucide-react';
import { AuthProvider, AuthContext } from './context/AuthContext';
import Login from './pages/Login';
import Register from './pages/Register';
import Subjects from './pages/Subjects';
import SubjectDetail from './pages/SubjectDetail';
import Study from './pages/Study';
import Analytics from './pages/Analytics';
import AiTutor from './pages/AiTutor';
import KnowledgeGraph from './pages/KnowledgeGraph';

const Sidebar = () => {
  const { user, logout } = useContext(AuthContext);

  return (
    <div className="w-64 border-r border-white/10 glass min-h-screen p-6 flex flex-col gap-6">
      <div className="flex items-center gap-3 text-2xl font-bold tracking-tight bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-500">
        <BrainCircuit className="text-purple-400" size={32} />
        <span>Arsps</span>
      </div>

      <nav className="flex flex-col gap-2 mt-8 flex-1">
        <Link to="/" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white">
          <Home size={20} /> Dashboard
        </Link>
        <Link to="/subjects" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white">
          <Library size={20} /> Subjects
        </Link>
        <Link to="/study" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white">
          <BookOpen size={20} /> Study Session
        </Link>
        <Link to="/graph" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white">
          <Network size={20} className="text-purple-400" /> Knowledge Graph
        </Link>
        <Link to="/analytics" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white">
          <BarChart3 size={20} /> Analytics
        </Link>
        <Link to="/ai-tutor" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-white/10 transition-colors text-slate-300 hover:text-white">
          <Bot size={20} className="text-blue-400" /> AI Tutor
        </Link>
      </nav>

      <div className="border-t border-white/10 pt-4 mt-auto">
        <div className="px-4 py-3 text-sm text-slate-400 mb-2 truncate">
          Logged in as <span className="text-white font-medium">{user?.username}</span>
        </div>
        <button 
          onClick={logout}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut size={20} /> Sign Out
        </button>
      </div>
    </div>
  );
};

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const [stats, setStats] = useState({ due_today: 0, overall_accuracy: 0, current_streak: 0, total_concepts: 0, total_reviews: 0 });
  const [distribution, setDistribution] = useState([]);
  const [weakConcepts, setWeakConcepts] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [ovRes, distRes, weakRes] = await Promise.all([
          api.get('/analytics/overview'),
          api.get('/analytics/distribution').catch(() => ({ data: [] })),
          api.get('/analytics/weak-concepts?limit=5').catch(() => ({ data: [] })),
        ]);
        setStats(ovRes.data);
        setDistribution(distRes.data);
        setWeakConcepts(weakRes.data);
      } catch (err) {
        console.error("Failed to load dashboard stats", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);
  
  const algoColors = { sm2: '#3b82f6', fsrs: '#8b5cf6', multi_fsrs: '#ec4899' };
  const algoLabels = { sm2: 'SM-2', fsrs: 'FSRS', multi_fsrs: 'Multi-FSRS' };
  const totalAlgo = distribution.reduce((a, d) => a + d.count, 0);

  return (
    <div className="p-8 max-w-6xl w-full">
      <h1 className="text-4xl font-bold mb-8">Welcome back, <span className="text-purple-400">{user?.username}</span></h1>
      
      {loading ? (
         <div className="flex justify-center p-12"><Loader2 className="animate-spin text-purple-500" size={32} /></div>
      ) : (
        <>
          {/* Top Stats Row */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Link to="/study" className="glass p-6 rounded-2xl group hover:border-purple-500/50 transition-colors cursor-pointer block relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-purple-600/10 to-pink-600/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <h3 className="text-sm text-slate-400 font-medium tracking-wide relative z-10">Due Today</h3>
              <p className="text-4xl font-bold mt-1 text-white relative z-10">{stats.due_today} <span className="text-base text-slate-400 font-normal">cards</span></p>
            </Link>
            <Link to="/analytics" className="glass p-6 rounded-2xl group hover:border-purple-500/50 transition-colors cursor-pointer block relative overflow-hidden">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-600/10 to-purple-600/10 opacity-0 group-hover:opacity-100 transition-opacity"></div>
              <h3 className="text-sm text-slate-400 font-medium tracking-wide relative z-10">Accuracy</h3>
              <p className="text-4xl font-bold mt-1 text-white relative z-10">{stats.overall_accuracy}<span className="text-base text-slate-400 font-normal">%</span></p>
            </Link>
            <div className="glass p-6 rounded-2xl">
              <h3 className="text-sm text-slate-400 font-medium tracking-wide">Streak</h3>
              <p className="text-4xl font-bold mt-1 text-white">{stats.current_streak} <span className="text-base text-slate-400 font-normal">days</span></p>
            </div>
            <div className="glass p-6 rounded-2xl">
              <h3 className="text-sm text-slate-400 font-medium tracking-wide">Total Concepts</h3>
              <p className="text-4xl font-bold mt-1 text-white">{stats.total_concepts}</p>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Algorithm Distribution */}
            {distribution.length > 0 && (
              <div className="glass p-6 rounded-2xl">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><BrainCircuit size={20} className="text-purple-400" /> Algorithm Distribution</h3>
                <div className="flex gap-2 h-4 rounded-full overflow-hidden mb-4">
                  {distribution.map(d => (
                    <div
                      key={d.algorithm}
                      style={{ width: `${(d.count / totalAlgo) * 100}%`, backgroundColor: algoColors[d.algorithm] || '#6b7280' }}
                      className="transition-all duration-500"
                    />
                  ))}
                </div>
                <div className="flex gap-6 text-sm">
                  {distribution.map(d => (
                    <div key={d.algorithm} className="flex items-center gap-2">
                      <span className="w-3 h-3 rounded-full" style={{ backgroundColor: algoColors[d.algorithm] || '#6b7280' }}></span>
                      <span className="text-slate-400">{algoLabels[d.algorithm] || d.algorithm}</span>
                      <span className="text-white font-bold">{d.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Weak Concepts */}
            {weakConcepts.length > 0 && (
              <div className="glass p-6 rounded-2xl">
                <h3 className="text-lg font-bold mb-4 flex items-center gap-2"><AlertTriangle size={20} className="text-amber-400" /> At-Risk Concepts</h3>
                <div className="space-y-3">
                  {weakConcepts.slice(0, 5).map(c => (
                    <div key={c.concept_id} className="flex items-center justify-between">
                      <span className="text-slate-300 text-sm truncate max-w-[200px]">{c.title}</span>
                      <div className="flex items-center gap-3">
                        <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                          <div
                            className="h-full rounded-full"
                            style={{
                              width: `${c.retrievability * 100}%`,
                              background: c.retrievability >= 0.5 ? '#f59e0b' : '#ef4444',
                            }}
                          />
                        </div>
                        <span className={`text-xs font-mono font-bold ${c.retrievability >= 0.5 ? 'text-amber-400' : 'text-red-400'}`}>
                          {(c.retrievability * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Link to="/study" className="glass p-6 rounded-2xl text-center hover:border-green-500/50 transition-colors group">
              <BookOpen size={36} className="mx-auto text-green-400 mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="text-lg font-bold">Start Studying</h3>
              <p className="text-slate-500 text-sm mt-1">Review your due concepts</p>
            </Link>
            <Link to="/graph" className="glass p-6 rounded-2xl text-center hover:border-purple-500/50 transition-colors group">
              <Network size={36} className="mx-auto text-purple-400 mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="text-lg font-bold">Knowledge Graph</h3>
              <p className="text-slate-500 text-sm mt-1">Visualize concept connections</p>
            </Link>
            <Link to="/ai-tutor" className="glass p-6 rounded-2xl text-center hover:border-blue-500/50 transition-colors group">
              <Bot size={36} className="mx-auto text-blue-400 mb-3 group-hover:scale-110 transition-transform" />
              <h3 className="text-lg font-bold">AI Tutor</h3>
              <p className="text-slate-500 text-sm mt-1">Generate flashcards with AI</p>
            </Link>
          </div>
        </>
      )}
    </div>
  );
};

const ProtectedLayout = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  const location = useLocation();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-950">
        <Loader2 className="animate-spin text-purple-500" size={48} />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return (
    <div className="flex bg-slate-950 text-white min-h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto">
        {children}
      </main>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/" element={<ProtectedLayout><Dashboard /></ProtectedLayout>} />
          <Route path="/subjects" element={<ProtectedLayout><Subjects /></ProtectedLayout>} />
          <Route path="/subjects/:id" element={<ProtectedLayout><SubjectDetail /></ProtectedLayout>} />
          <Route path="/study" element={<ProtectedLayout><Study /></ProtectedLayout>} />
          <Route path="/graph" element={<ProtectedLayout><KnowledgeGraph /></ProtectedLayout>} />
          <Route path="/analytics" element={<ProtectedLayout><Analytics /></ProtectedLayout>} />
          <Route path="/ai-tutor" element={<ProtectedLayout><AiTutor /></ProtectedLayout>} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
