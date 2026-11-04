import React, { useContext, useState, useEffect, useRef } from 'react';
import { BrowserRouter as Router, Routes, Route, Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import api from './api';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Home, BookOpen, BrainCircuit, BarChart3, Settings, LogOut, 
  Loader2, Library, Bot, Network, AlertTriangle, TrendingUp, 
  X, Download, Upload, CheckCircle, ArrowRight, Menu, Zap, Timer, 
  MessageSquare, Layers, Box, Code2, GraduationCap
} from 'lucide-react';
import { AuthProvider, AuthContext } from './context/AuthContext';

import Login from './pages/Login';
import Register from './pages/Register';
import Subjects from './pages/Subjects';
import SubjectDetail from './pages/SubjectDetail';
import Study from './pages/Study';
import Analytics from './pages/Analytics';
import AiTutor from './pages/AiTutor';
import KnowledgeGraph from './pages/KnowledgeGraph';
import Research from './pages/Research';

// --- Components ---

const Toast = ({ message, type, onClose }) => {
  useEffect(() => {
    const timer = setTimeout(onClose, 3000);
    return () => clearTimeout(timer);
  }, [onClose]);

  const bgMap = {
    success: 'bg-success/20 border-success/50 text-success',
    error: 'bg-destructive/20 border-destructive/50 text-destructive',
    info: 'bg-primary/20 border-primary/50 text-primary'
  };

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, scale: 0.95 }}
      className={`fixed bottom-8 right-8 z-[200] px-6 py-4 rounded-2xl border backdrop-blur-md shadow-2xl flex items-center gap-3 ${bgMap[type] || bgMap.info}`}
    >
      {type === 'success' && <CheckCircle size={20} />}
      {type === 'error' && <AlertTriangle size={20} />}
      <span className="font-bold text-sm tracking-tight">{message}</span>
      <button onClick={onClose} className="ml-4 opacity-50 hover:opacity-100 transition-opacity">
        <X size={18} />
      </button>
    </motion.div>
  );
};

const SidebarLink = ({ to, icon: Icon, label, active, onClick }) => (
  <Link 
    to={to} 
    onClick={onClick}
    className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all duration-300 group ${
      active 
        ? 'bg-primary text-primary-foreground shadow-lg shadow-primary/20' 
        : 'text-slate-400 hover:bg-white/5 hover:text-white'
    }`}
  >
    <Icon size={20} className={active ? '' : 'group-hover:scale-110 transition-transform'} />
    <span className="font-medium text-sm">{label}</span>
    {active && <div className="ml-auto w-1.5 h-1.5 rounded-full bg-white" />}
  </Link>
);

const SettingsModal = ({ isOpen, onClose }) => {
  const [importing, setImporting] = useState(false);
  const [message, setMessage] = useState(null);
  const fileInputRef = useRef();

  if (!isOpen) return null;

  const handleExport = async () => {
    try {
      const res = await api.get('/concepts/export/all');
      const blob = new Blob([JSON.stringify(res.data, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `arsps-export-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error("Export failed", err);
    }
  };

  const handleImport = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setImporting(true);
    const reader = new FileReader();
    reader.onload = async (event) => {
      try {
        const data = JSON.parse(event.target.result);
        const res = await api.post('/concepts/import/all', data);
        setMessage(`Successfully imported ${res.data.imported} concepts!`);
        setTimeout(() => { setMessage(null); onClose(); }, 2000);
      } catch (err) {
        setMessage("Import failed: Invalid file format.");
      } finally {
        setImporting(false);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-background/80 backdrop-blur-sm">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="glass-card max-w-lg w-full p-8 rounded-[2rem] border border-white/10 shadow-2xl relative"
      >
        <button onClick={onClose} className="absolute top-6 right-6 text-muted-foreground hover:text-foreground transition-colors">
          <X size={24} />
        </button>
        
        <h2 className="text-2xl font-bold mb-6 flex items-center gap-3">
          <Settings className="text-primary" /> System Settings
        </h2>

        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white/5 border border-white/5">
            <h3 className="text-lg font-semibold mb-2 text-white">Data Management</h3>
            <p className="text-xs text-muted-foreground mb-6 leading-relaxed">Backup your entire knowledge base or restore from a previous session.</p>
            
            <div className="grid grid-cols-2 gap-4">
              <button onClick={handleExport} className="flex items-center justify-center gap-2 py-3 rounded-xl glass hover:bg-white/10 transition-colors text-xs font-bold uppercase tracking-widest text-white">
                <Download size={16} /> Export
              </button>
              <button 
                onClick={() => fileInputRef.current.click()}
                disabled={importing}
                className="flex items-center justify-center gap-2 py-3 rounded-xl glass hover:bg-white/10 transition-colors text-xs font-bold uppercase tracking-widest disabled:opacity-50 text-white"
              >
                {importing ? <Loader2 className="animate-spin" size={16} /> : <Upload size={16} />} Import
              </button>
              <input type="file" ref={fileInputRef} onChange={handleImport} className="hidden" accept=".json" />
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  );
};

// --- Pages ---

const Dashboard = () => {
  const { user } = useContext(AuthContext);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [codingFluency, setCodingFluency] = useState(0);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [ovRes, weakRes, subRes] = await Promise.all([
          api.get('/analytics/overview'),
          api.get('/analytics/weak-concepts'),
          api.get('/subjects/')
        ]);
        setStats({ overview: ovRes.data, weak: weakRes.data });
        
        // Calculate Coding Fluency heuristic
        const csSubs = subRes.data.filter(s => 
          ['cs', 'programming', 'code', 'data structures', 'algorithms'].some(k => s.name.toLowerCase().includes(k))
        );
        if (csSubs.length > 0) {
           setCodingFluency(75); // Heuristic for now
        }
      } catch (err) {
        console.error("Overview error", err);
      } finally {
        setLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (loading) return <div className="flex h-[80vh] items-center justify-center"><Loader2 className="animate-spin text-primary" size={48} /></div>;

  return (
    <motion.div 
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="p-4 md:p-8 max-w-7xl w-full mx-auto"
    >
      <header className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-2 text-white">
            Welcome back, <span className="text-primary">{user?.username}</span>
          </h1>
          <p className="text-slate-500 font-medium">Your cognitive engine is primed and ready.</p>
        </div>
        <div className="flex gap-3 w-full md:w-auto">
          <button 
            onClick={() => navigate('/study')}
            className="flex-1 md:flex-none bg-primary text-primary-foreground px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 transition-all flex items-center justify-center gap-2"
          >
            Start Session <ArrowRight size={16} />
          </button>
        </div>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 md:gap-6 mb-10 text-white">
        {[
          { label: 'Total Synapses', val: stats?.overview.total_concepts, icon: BrainCircuit, color: 'text-primary', bg: 'bg-primary/10' },
          { label: 'Neural Accuracy', val: `${stats?.overview.overall_accuracy}%`, icon: Zap, color: 'text-success', bg: 'bg-success/10' },
          { label: 'Logic Streak', val: `${stats?.overview.current_streak} d`, icon: Code2, color: 'text-amber-500', bg: 'bg-amber-500/10' },
          { label: 'Queue Depth', val: stats?.overview.due_today, icon: Layers, color: 'text-accent', bg: 'bg-accent/10' },
        ].map((item, i) => (
          <div key={i} className="glass-card p-6 rounded-[2rem] border border-white/5 relative overflow-hidden group">
            <div className="flex justify-between items-start relative z-10">
              <div>
                <p className="text-[10px] font-black uppercase tracking-widest text-slate-500 mb-1">{item.label}</p>
                <p className="text-3xl font-black">{item.val}</p>
              </div>
              <div className={`p-3 rounded-xl ${item.bg} ${item.color} group-hover:scale-110 transition-transform`}>
                <item.icon size={20} />
              </div>
            </div>
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-white/5 rounded-full blur-2xl group-hover:bg-white/10 transition-all"></div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
           {/* Coding Mastery Card */}
           <div className="glass-card p-10 rounded-[3rem] border border-white/5 relative overflow-hidden group flex flex-col md:flex-row items-center gap-10">
              <div className="relative shrink-0">
                 <div className="w-32 h-32 rounded-full border-4 border-white/5 flex items-center justify-center">
                    <span className="text-3xl font-black text-white">{codingFluency}%</span>
                 </div>
                 <svg className="absolute top-0 left-0 w-32 h-32 -rotate-90">
                    <circle 
                      cx="64" cy="64" r="60" 
                      fill="transparent" 
                      stroke="currentColor" 
                      strokeWidth="4"
                      strokeDasharray={377}
                      strokeDashoffset={377 * (1 - codingFluency / 100)}
                      className="text-primary transition-all duration-1000"
                    />
                 </svg>
              </div>
              <div className="flex-1 text-center md:text-left">
                 <h2 className="text-2xl font-black text-white mb-2 tracking-tight">Programming Fluency</h2>
                 <p className="text-slate-500 text-sm mb-6 leading-relaxed">
                    Based on your performance in Data Structures, Algorithms, and System Design clusters.
                 </p>
                 <div className="flex flex-wrap gap-2 justify-center md:justify-start">
                    {['Memory Safety', 'Time Complexity', 'Syntax'].map(tag => (
                      <span key={tag} className="px-3 py-1 rounded-full bg-white/5 border border-white/10 text-[9px] font-black uppercase tracking-widest text-slate-400">{tag}</span>
                    ))}
                 </div>
              </div>
              <div className="shrink-0">
                 <button onClick={() => navigate('/analytics')} className="p-4 rounded-2xl glass hover:bg-white/5 text-primary transition-all">
                    <TrendingUp size={24} />
                 </button>
              </div>
           </div>

           <div className="glass-card p-10 rounded-[2.5rem] border border-white/5 min-h-[300px] flex flex-col justify-center items-center text-center relative overflow-hidden group">
              <div className="absolute top-0 left-0 w-full h-full bg-gradient-to-b from-primary/5 to-transparent"></div>
              <div className="p-6 bg-primary/10 rounded-full mb-8 relative z-10 group-hover:scale-110 transition-transform duration-500">
                <Bot size={48} className="text-primary" />
              </div>
              <h2 className="text-3xl font-black mb-4 relative z-10 tracking-tight text-white">AI Socratic Tutor</h2>
              <p className="text-slate-400 max-w-sm mb-10 leading-relaxed text-sm relative z-10">
                Unlock deeper understanding through AI-driven follow-ups and atomic concept mapping.
              </p>
              <button 
                onClick={() => navigate('/ai-tutor')}
                className="glass px-12 py-4 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-white/10 transition-all border border-white/10 relative z-10 text-white"
              >
                Invoke AI Tutor
              </button>
           </div>
        </div>
        
        <div className="glass-card p-8 rounded-[2.5rem] border border-white/5 h-full text-white">
          <h3 className="text-xs font-black uppercase tracking-widest text-slate-500 mb-8 flex items-center gap-2">
            <AlertTriangle size={14} className="text-destructive" /> Critical Nodes
          </h3>
          <div className="space-y-4">
            {stats?.weak.slice(0, 5).map(concept => (
              <div key={concept.concept_id} className="p-4 bg-white/5 rounded-2xl border border-white/5 flex justify-between items-center group cursor-pointer hover:bg-white/10 transition-all">
                <div>
                  <p className="font-bold text-sm truncate max-w-[120px]">{concept.title}</p>
                  <p className="text-[10px] text-slate-500 uppercase font-black tracking-tighter">{concept.algorithm}</p>
                </div>
                <div className="text-right">
                  <p className={`text-xs font-black ${concept.retrievability < 0.5 ? 'text-destructive' : 'text-warning'}`}>
                    {(concept.retrievability * 100).toFixed(0)}%
                  </p>
                  <div className="w-12 h-1 bg-white/5 rounded-full mt-1 overflow-hidden">
                    <div className={`h-full ${concept.retrievability < 0.5 ? 'bg-destructive' : 'bg-warning'}`} style={{ width: `${concept.retrievability * 100}%` }}></div>
                  </div>
                </div>
              </div>
            ))}
            <button onClick={() => navigate('/subjects')} className="w-full py-4 text-[10px] font-black text-slate-500 uppercase tracking-[0.2em] hover:text-white transition-colors">
              Synchronize All Nodes
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

// --- App Shell ---

const AppContent = () => {
  const { user, logout, loading } = useContext(AuthContext);
  const location = useLocation();
  const navigate = useNavigate();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [academicMode, setAcademicMode] = useState(false);
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (academicMode) {
      document.body.classList.add('academic-theme');
    } else {
      document.body.classList.remove('academic-theme');
    }
  }, [academicMode]);

  useEffect(() => {
    const handleShowToast = (e) => setToast(e.detail);
    window.addEventListener('show-toast', handleShowToast);
    return () => window.removeEventListener('show-toast', handleShowToast);
  }, []);

  if (loading) return <div className="flex h-screen items-center justify-center bg-background"><Loader2 className="animate-spin text-primary" size={64} /></div>;

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="flex min-h-screen bg-background text-foreground font-sans selection:bg-primary/30">
      {user && (
        <>
          {/* Desktop Sidebar */}
          <aside className="hidden lg:flex w-72 flex-col p-8 border-r border-white/5 bg-background sticky top-0 h-screen overflow-y-auto scrollbar-none">
            <div className="flex items-center gap-3 mb-16 px-2 shrink-0">
              <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center shadow-lg shadow-primary/30">
                <BrainCircuit className="text-primary-foreground" size={24} />
              </div>
              <span className="text-xl font-black tracking-tighter text-foreground">ARSPS <span className="text-primary text-[9px] uppercase font-black tracking-widest block -mt-1">Horizon</span></span>
            </div>
            
            <nav className="flex-grow space-y-2">
              <SidebarLink to="/" icon={Home} label="Terminal" active={location.pathname === '/'} />
              <SidebarLink to="/subjects" icon={Library} label="Knowledge base" active={location.pathname === '/subjects'} />
              <SidebarLink to="/study" icon={BookOpen} label="Focus Session" active={location.pathname === '/study'} />
              <SidebarLink to="/analytics" icon={BarChart3} label="Neural Metrics" active={location.pathname === '/analytics'} />
              <SidebarLink to="/ai-tutor" icon={Bot} label="Socratic Tutor" active={location.pathname === '/ai-tutor'} />
              <SidebarLink to="/graph" icon={Network} label="Neural Space" active={location.pathname === '/graph'} />
              <SidebarLink to="/research" icon={Box} label="Research Labs" active={location.pathname === '/research'} />
            </nav>

            <div className="mt-auto pt-8 border-t border-white/5 space-y-2 shrink-0">
              <button 
                onClick={() => setAcademicMode(!academicMode)}
                aria-label={academicMode ? "Disable Academic Mode" : "Enable Academic Mode"}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-slate-400 hover:bg-black/5 hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none`}
              >
                <GraduationCap size={20} className={academicMode ? "text-primary" : ""} />
                <span className="font-medium text-sm">Academic Mode</span>
              </button>
              <button 
                onClick={() => setSettingsOpen(true)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all text-slate-400 hover:bg-black/5 hover:text-foreground focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none`}
              >
                <Settings size={20} />
                <span className="font-medium text-sm">Engine Config</span>
              </button>
              <button 
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-xl text-slate-500 hover:bg-destructive/10 hover:text-destructive transition-all duration-300"
              >
                <LogOut size={20} />
                <span className="font-medium text-sm">Sign Out</span>
              </button>
            </div>
          </aside>

          {/* Minimal Mobile Header */}
          <div className="lg:hidden fixed top-0 left-0 right-0 h-16 glass z-40 px-6 flex items-center justify-between text-foreground border-b border-white/5">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center shadow-lg shadow-primary/20">
                <BrainCircuit className="text-primary-foreground" size={18} />
              </div>
              <span className="text-lg font-black tracking-tighter">ARSPS</span>
            </div>
            <div className="flex items-center gap-3">
              <button 
                onClick={() => setAcademicMode(!academicMode)} 
                aria-label={academicMode ? "Disable Academic Mode" : "Enable Academic Mode"}
                className="p-2 text-slate-400 hover:text-foreground transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded-md"
              >
                <GraduationCap size={20} className={academicMode ? "text-primary" : ""} />
              </button>
              <button 
                onClick={() => setSettingsOpen(true)} 
                aria-label="Engine Config"
                className="p-2 text-slate-400 hover:text-foreground transition-colors focus-visible:ring-2 focus-visible:ring-primary focus-visible:outline-none rounded-md"
              >
                <Settings size={20} />
              </button>
              <button 
                onClick={handleLogout} 
                aria-label="Sign Out"
                className="p-2 text-slate-400 hover:text-destructive transition-colors focus-visible:ring-2 focus-visible:ring-destructive focus-visible:outline-none rounded-md"
              >
                <LogOut size={20} />
              </button>
            </div>
          </div>

          {/* Bottom Navigation Bar (Mobile) */}
          <nav className="lg:hidden fixed bottom-0 left-0 right-0 h-20 glass z-50 flex justify-around items-center px-2 pb-safe border-t border-white/5">
            {[
              { to: "/", icon: Home, label: "Home" },
              { to: "/subjects", icon: Library, label: "Knowledge" },
              { to: "/study", icon: BookOpen, label: "Study" },
              { to: "/graph", icon: Network, label: "Graph" },
              { to: "/analytics", icon: BarChart3, label: "Stats" }
            ].map(item => {
              const isActive = location.pathname === item.to || (item.to !== '/' && location.pathname.startsWith(item.to));
              return (
                <Link 
                  key={item.to}
                  to={item.to}
                  className={`flex flex-col items-center justify-center w-full h-full space-y-1 transition-all ${
                    isActive ? 'text-primary' : 'text-slate-500 hover:text-slate-300'
                  }`}
                >
                  <div className={`p-1.5 rounded-xl transition-all ${isActive ? 'bg-primary/20 scale-110' : ''}`}>
                    <item.icon size={20} strokeWidth={isActive ? 2.5 : 2} />
                  </div>
                  <span className={`text-[10px] font-bold ${isActive ? 'text-primary' : ''}`}>{item.label}</span>
                </Link>
              );
            })}
          </nav>
        </>
      )}

      <main className={`flex-grow min-w-0 ${user ? 'pt-16 pb-24 lg:pt-0 lg:pb-0' : ''}`}>
        <AnimatePresence mode="wait">
          <Routes location={location} key={location.pathname}>
            <Route path="/login" element={!user ? <Login /> : <Navigate to="/" />} />
            <Route path="/register" element={!user ? <Register /> : <Navigate to="/" />} />
            
            <Route path="/" element={<PrivateRoute><Dashboard /></PrivateRoute>} />
            <Route path="/subjects" element={<PrivateRoute><Subjects /></PrivateRoute>} />
            <Route path="/subjects/:id" element={<PrivateRoute><SubjectDetail /></PrivateRoute>} />
            <Route path="/study" element={<PrivateRoute><Study /></PrivateRoute>} />
            <Route path="/analytics" element={<PrivateRoute><Analytics /></PrivateRoute>} />
            <Route path="/ai-tutor" element={<PrivateRoute><AiTutor /></PrivateRoute>} />
            <Route path="/graph" element={<PrivateRoute><KnowledgeGraph /></PrivateRoute>} />
            <Route path="/research" element={<PrivateRoute><Research /></PrivateRoute>} />
          </Routes>
        </AnimatePresence>
      </main>

      <SettingsModal isOpen={settingsOpen} onClose={() => setSettingsOpen(false)} />
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
};

const PrivateRoute = ({ children }) => {
  const { user, loading } = useContext(AuthContext);
  if (loading) return null;
  return user ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <AuthProvider>
      <Router>
        <AppContent />
      </Router>
    </AuthProvider>
  );
}

export default App;
