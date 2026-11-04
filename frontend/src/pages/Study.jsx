import React, { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Loader2, CheckCircle, BookOpen, Bot, FastForward, Flag, ArrowRight, 
  Zap, Timer, Award, MessageSquare, Code2, Sparkles, Trophy, ArrowLeft,
  Layers, GraduationCap, Play, RefreshCw, Filter, Check, ChevronRight,
  Globe
} from 'lucide-react';
import api, { showToast } from '../api';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import CodeEditor from './CodeEditor';

const parseSubId = (val) => {
  if (!val) return null;
  if (val === 'all') return 'all';
  const parsed = parseInt(val);
  return isNaN(parsed) ? null : parsed;
};

const Study = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const queryParams = new URLSearchParams(location.search);
  
  const initialSubjectParam = queryParams.get('subject_id') || queryParams.get('subject');
  const initialExamSubjectId = queryParams.get('exam_subject_id');
  const initialConceptId = queryParams.get('concept') || queryParams.get('concept_id');

  // Active Subject State: 'all' | number | null
  const [selectedSubjectId, setSelectedSubjectId] = useState(
    initialSubjectParam ? parseSubId(initialSubjectParam) : (initialExamSubjectId ? parseInt(initialExamSubjectId) : null)
  );
  const [isExamMode, setIsExamMode] = useState(!!initialExamSubjectId);
  const [availableSubjects, setAvailableSubjects] = useState([]);
  const [subjectStats, setSubjectStats] = useState({});
  const [loadingSubjects, setLoadingSubjects] = useState(false);

  // Card queue & review states
  const [dueConcepts, setDueConcepts] = useState([]);
  const [loadingQueue, setLoadingQueue] = useState(false);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  // Phase management: 'question' | 'grading' | 'finished'
  const [phase, setPhase] = useState('question'); 
  const [typedAnswer, setTypedAnswer] = useState('');
  const [codeSnippet, setCodeSnippet] = useState('');
  const [followUpAnswer, setFollowUpAnswer] = useState('');
  const [isAiLoading, setIsAiLoading] = useState(false);
  const [aiEvaluation, setAiEvaluation] = useState(null);
  
  // Session tracking
  const [startTime, setStartTime] = useState(null);
  const [cardStartTime, setCardStartTime] = useState(null);
  const [cardTimer, setCardTimer] = useState(0);
  const timerRef = useRef(null);

  // Sync state when URL params change
  useEffect(() => {
    const sId = queryParams.get('subject_id') || queryParams.get('subject');
    const examId = queryParams.get('exam_subject_id');
    if (examId) {
      setSelectedSubjectId(parseInt(examId));
      setIsExamMode(true);
    } else if (sId) {
      setSelectedSubjectId(parseSubId(sId));
      setIsExamMode(false);
    }
  }, [location.search]);

  // Fetch all available subjects if no subject is selected yet
  useEffect(() => {
    const loadSubjectsList = async () => {
      setLoadingSubjects(true);
      try {
        const [subRes, dueRes] = await Promise.all([
          api.get('/subjects/'),
          api.get('/reviews/due')
        ]);
        const subs = subRes.data;
        setAvailableSubjects(subs);

        // Count due cards per subject
        const dueMap = {};
        (dueRes.data || []).forEach(c => {
          const matchedSub = subs.find(s => s.name === c.subject_name);
          if (matchedSub) {
            dueMap[matchedSub.id] = (dueMap[matchedSub.id] || 0) + 1;
          }
        });

        // Get count and avg retrievability per subject
        const stats = {};
        await Promise.all(
          subs.map(async (sub) => {
            try {
              const cRes = await api.get(`/concepts/?subject_id=${sub.id}`);
              const concepts = cRes.data;
              let totalR = 0;
              let countWithR = 0;
              for (const c of concepts.slice(0, 15)) {
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
                dueCount: dueMap[sub.id] || 0,
                avgR: countWithR > 0 ? (totalR / countWithR) : 1.0
              };
            } catch {
              stats[sub.id] = { count: 0, dueCount: 0, avgR: 1.0 };
            }
          })
        );
        setSubjectStats(stats);
      } catch (err) {
        showToast("Failed to load subjects for study selection", "error");
      } finally {
        setLoadingSubjects(false);
      }
    };

    if (!selectedSubjectId) {
      loadSubjectsList();
    }
  }, [selectedSubjectId]);

  // Fetch queue when a subject or 'all' is active
  const fetchQueueForSubject = useCallback(async (subjectId, examMode = false, includeAll = false) => {
    if (!subjectId) return;
    setLoadingQueue(true);
    try {
      let endpoint = '';
      if (subjectId === 'all') {
        endpoint = `/reviews/due${includeAll ? '?include_all=true' : ''}`;
      } else if (examMode) {
        endpoint = `/reviews/exam/${subjectId}`;
      } else {
        endpoint = `/reviews/due?subject_id=${subjectId}${includeAll ? '&include_all=true' : ''}`;
      }
      
      const res = await api.get(endpoint);
      let queue = res.data || [];

      // If a specific concept ID was targeted (e.g. from Knowledge Graph), prioritize it
      if (initialConceptId) {
        const targetId = parseInt(initialConceptId);
        const targetIndex = queue.findIndex(c => c.concept_id === targetId);
        if (targetIndex > 0) {
          const [targetConcept] = queue.splice(targetIndex, 1);
          queue.unshift(targetConcept);
        }
      }

      setDueConcepts(queue);
      setCurrentIndex(0);
      setPhase('question');
      setTypedAnswer('');
      setCodeSnippet('');
      setFollowUpAnswer('');
      setAiEvaluation(null);
      setStartTime(Date.now());
      setCardStartTime(Date.now());
      setCardTimer(0);

      if (examMode) {
        showToast("Exam Protocol: High-Intensity Logic Re-routing", "info");
      }
    } catch (err) {
      showToast("Failed to load study queue", "error");
    } finally {
      setLoadingQueue(false);
    }
  }, [initialConceptId]);

  useEffect(() => {
    if (selectedSubjectId) {
      fetchQueueForSubject(selectedSubjectId, isExamMode);
    }
  }, [selectedSubjectId, isExamMode, fetchQueueForSubject]);

  // Select subject handler ('all' | number)
  const handleSelectSubject = (subjectId, examMode = false) => {
    setSelectedSubjectId(subjectId);
    setIsExamMode(examMode);
    if (subjectId === 'all') {
      navigate('/study?subject_id=all', { replace: true });
    } else {
      const paramName = examMode ? 'exam_subject_id' : 'subject_id';
      navigate(`/study?${paramName}=${subjectId}`, { replace: true });
    }
  };

  // Switch subject back to selector
  const handleSwitchSubject = () => {
    setSelectedSubjectId(null);
    setIsExamMode(false);
    setDueConcepts([]);
    setCurrentIndex(0);
    setPhase('question');
    navigate('/study', { replace: true });
  };

  // Card Timer Logic
  useEffect(() => {
    if (phase === 'question' && !loadingQueue && dueConcepts.length > 0) {
      timerRef.current = setInterval(() => {
        setCardTimer(Math.floor((Date.now() - (cardStartTime || Date.now())) / 1000));
      }, 1000);
    } else {
      clearInterval(timerRef.current);
    }
    return () => clearInterval(timerRef.current);
  }, [phase, loadingQueue, dueConcepts, cardStartTime]);

  const handleNextCard = () => {
    if (currentIndex < dueConcepts.length - 1) {
      setCurrentIndex(prev => prev + 1);
      setPhase('question');
      setTypedAnswer('');
      setCodeSnippet('');
      setFollowUpAnswer('');
      setAiEvaluation(null);
      setCardStartTime(Date.now());
      setCardTimer(0);
    } else {
      setPhase('finished');
    }
  };

  const handleAiGrade = async () => {
    if (!typedAnswer.trim() && !codeSnippet.trim()) {
      showToast("Please provide an answer or write some code", "info");
      return;
    }
    setIsAiLoading(true);
    setPhase('grading');
    try {
      const currentConcept = dueConcepts[currentIndex];
      let fullAnswer = typedAnswer;
      if (codeSnippet) {
        fullAnswer = `CODE SNIPPET:\n\`\`\`\n${codeSnippet}\n\`\`\`\n\nLOGIC EXPLANATION:\n${typedAnswer}`;
      }
      
      const res = await api.post('/ai/evaluate-answer', {
        concept_id: currentConcept.concept_id,
        typed_answer: fullAnswer
      });
      setAiEvaluation(res.data);
    } catch (err) {
      console.error("AI grading error:", err);
      showToast("AI grading failed. Please self-grade.", "warning");
      setAiEvaluation({
        feedback_markdown: "AI service was unable to grade this response. Please compare your answer manually.",
        sm2_score: 3,
        fsrs_score: 3
      });
    } finally {
      setIsAiLoading(false);
    }
  };

  const submitFinalGrade = async (rating) => {
    const currentConcept = dueConcepts[currentIndex];
    try {
      await api.post('/reviews/submit', {
        concept_id: currentConcept.concept_id,
        quality_score: rating,
        was_correct: rating > 1, 
        response_time_sec: cardTimer
      });
      showToast("Neural link updated", "success");
      handleNextCard();
    } catch (err) {
      showToast("Failed to save review", "error");
    }
  };

  const handleSkip = () => {
    const currentConcept = dueConcepts[currentIndex];
    const failScore = currentConcept.algorithm === 'sm2' ? 0 : 1;
    submitFinalGrade(failScore);
  };

  // Keyboard Hotkeys
  const handleKeyDown = useCallback((e) => {
    if (phase === 'question') {
      if (e.key === 'Enter' && e.ctrlKey && (typedAnswer.trim() || codeSnippet.trim())) handleAiGrade();
    } else if (phase === 'grading' && !isAiLoading) {
      if (['1', '2', '3', '4'].includes(e.key)) {
        submitFinalGrade(parseInt(e.key));
      }
    }
  }, [phase, typedAnswer, codeSnippet, isAiLoading]);

  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [handleKeyDown]);

  const currentCard = dueConcepts[currentIndex];
  const progress = ((currentIndex) / (dueConcepts.length || 1)) * 100;
  
  // Find active subject details
  const activeSubjectName = useMemo(() => {
    if (selectedSubjectId === 'all') return 'All Subjects (Master Queue)';
    if (currentCard?.subject_name) return currentCard.subject_name;
    const s = availableSubjects.find(sub => sub.id === selectedSubjectId);
    return s ? s.name : 'Selected Subject';
  }, [currentCard, availableSubjects, selectedSubjectId]);

  // Aggregate stats across all subjects
  const { totalGlobalCards, totalGlobalDue, avgGlobalR } = useMemo(() => {
    let totalC = 0;
    let totalD = 0;
    let totalR = 0;
    const subCount = availableSubjects.length || 1;
    availableSubjects.forEach(s => {
      const st = subjectStats[s.id] || { count: 0, dueCount: 0, avgR: 1.0 };
      totalC += st.count;
      totalD += st.dueCount;
      totalR += st.avgR;
    });
    return {
      totalGlobalCards: totalC,
      totalGlobalDue: totalD,
      avgGlobalR: totalR / subCount
    };
  }, [availableSubjects, subjectStats]);

  // Parse JSON-based Card structure (Front/Back)
  const { displayFront, displayBack } = useMemo(() => {
    if (!currentCard) return { displayFront: '', displayBack: '' };
    try {
      if (currentCard.concept_content && currentCard.concept_content.trim().startsWith('{')) {
        const parsed = JSON.parse(currentCard.concept_content);
        if (parsed.front !== undefined && parsed.back !== undefined) {
          return { displayFront: parsed.front, displayBack: parsed.back };
        }
      }
    } catch (e) { /* fallback */ }
    return { displayFront: currentCard.concept_title, displayBack: currentCard.concept_content };
  }, [currentCard]);

  // Improved CS Subject detection
  const isCodeSubject = useMemo(() => {
    if (!currentCard) return false;
    return [
      'code', 'c++', 'javascript', 'python', 'java', 'ds', 'algo', 'programming', 'oop'
    ].some(k => currentCard.subject_name?.toLowerCase().includes(k) || displayFront?.toLowerCase().includes(k));
  }, [currentCard, displayFront]);

  // ==========================================
  // VIEW 1: SUBJECT SELECTOR SCREEN
  // ==========================================
  if (!selectedSubjectId) {
    return (
      <div className="p-4 md:p-12 max-w-7xl w-full mx-auto animate-in fade-in duration-500 text-white space-y-10">
        <div className="text-center md:text-left">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-2xl bg-primary/10 border border-primary/20 text-primary text-[10px] font-black uppercase tracking-widest mb-4">
            <BookOpen size={14} /> Study Hub
          </div>
          <h1 className="text-4xl md:text-5xl font-black tracking-tight mb-3">
            Choose Study Mode
          </h1>
          <p className="text-slate-400 text-base max-w-2xl leading-relaxed">
            Choose to study <strong>all subjects at once</strong> for full-spectrum interleaved learning, or focus on a <strong>single subject</strong>.
          </p>
        </div>

        {loadingSubjects ? (
          <div className="flex flex-col items-center justify-center py-24 gap-4">
            <Loader2 className="animate-spin text-primary" size={48} />
            <p className="text-[10px] font-black uppercase tracking-[0.3em] text-slate-500">Loading Available Study Queues</p>
          </div>
        ) : availableSubjects.length === 0 ? (
          <div className="glass-card p-16 rounded-[3rem] border border-dashed border-white/10 text-center max-w-lg mx-auto space-y-6">
            <GraduationCap size={64} className="mx-auto text-slate-600" />
            <h3 className="text-2xl font-bold">No subjects found</h3>
            <p className="text-slate-400 text-sm">Create a subject and add concepts before starting a study session.</p>
            <Link 
              to="/subjects" 
              className="inline-flex items-center gap-2 bg-primary text-primary-foreground px-8 py-3.5 rounded-2xl font-black text-xs uppercase tracking-widest hover:scale-105 transition-all shadow-xl shadow-primary/20"
            >
              Go to Knowledge Base <ArrowRight size={16} />
            </Link>
          </div>
        ) : (
          <div className="space-y-10">
            {/* FEATURED: ALL SUBJECTS (GLOBAL MASTER QUEUE) */}
            <div className="glass-card p-8 md:p-10 rounded-[3rem] border-2 border-primary/30 bg-gradient-to-r from-violet-950/40 via-purple-950/30 to-indigo-950/40 relative overflow-hidden shadow-2xl group transition-all hover:border-primary/60">
              <div className="absolute top-0 right-0 w-96 h-96 bg-primary/15 rounded-full -translate-y-48 translate-x-48 blur-3xl pointer-events-none group-hover:bg-primary/25 transition-all"></div>

              <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-8 relative z-10">
                <div className="space-y-4 max-w-2xl">
                  <div className="flex flex-wrap items-center gap-3">
                    <div className="p-3 bg-primary/20 rounded-2xl text-primary border border-primary/30">
                      <Globe size={26} />
                    </div>
                    <span className="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-wider bg-primary/20 text-primary border border-primary/30 flex items-center gap-1.5">
                      <Sparkles size={10} /> Full Spectrum Review
                    </span>
                    {totalGlobalDue > 0 ? (
                      <span className="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-wider bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 animate-pulse">
                        {totalGlobalDue} Total Due Today
                      </span>
                    ) : (
                      <span className="px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider bg-white/5 text-slate-400 border border-white/5">
                        {totalGlobalCards} Total Cards
                      </span>
                    )}
                  </div>

                  <div>
                    <h2 className="text-3xl md:text-4xl font-black text-white tracking-tight">
                      All Subjects (Global Review)
                    </h2>
                    <p className="text-slate-300 text-sm mt-2 leading-relaxed">
                      Interleave concepts from all your subjects (<span className="text-primary font-bold">{availableSubjects.map(s => s.name).join(', ')}</span>) in a unified master queue for maximum long-term memory consolidation.
                    </p>
                  </div>

                  <div className="flex flex-wrap gap-6 pt-2 text-xs text-slate-400">
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-0.5">Domains</span>
                      <span className="text-white font-black text-base">{availableSubjects.length} Subjects</span>
                    </div>
                    <div className="w-px h-8 bg-white/10"></div>
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-0.5">Total Synapses</span>
                      <span className="text-white font-black text-base">{totalGlobalCards} Concepts</span>
                    </div>
                    <div className="w-px h-8 bg-white/10"></div>
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-widest text-slate-500 block mb-0.5">Global Retention</span>
                      <span className="text-emerald-400 font-mono font-black text-base">{((avgGlobalR || 1) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>

                {/* Global Action Buttons */}
                <div className="flex flex-col sm:flex-row lg:flex-col gap-3 w-full lg:w-72 shrink-0">
                  <button
                    onClick={() => handleSelectSubject('all', false)}
                    className="w-full py-4 px-6 bg-gradient-to-r from-violet-600 via-primary to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-2xl shadow-primary/30 hover:scale-105 active:scale-95 transition-all flex items-center justify-center gap-2"
                  >
                    <Play size={16} className="fill-current" /> Study All Subjects
                  </button>
                  <button
                    onClick={() => fetchQueueForSubject('all', false, true).then(() => {
                      setSelectedSubjectId('all');
                      navigate('/study?subject_id=all&mode=all', { replace: true });
                    })}
                    className="w-full py-3 px-6 bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white rounded-xl font-bold text-[10px] uppercase tracking-wider border border-white/10 transition-all flex items-center justify-center gap-1.5"
                    title="Review all concepts across all subjects regardless of due date"
                  >
                    <RefreshCw size={12} /> Master Practice Mode
                  </button>
                </div>
              </div>
            </div>

            {/* OR DIVIDER */}
            <div className="flex items-center gap-4 py-2">
              <div className="h-px bg-white/10 flex-1"></div>
              <span className="text-xs font-black uppercase tracking-[0.25em] text-slate-500">
                Or Focus on a Single Subject
              </span>
              <div className="h-px bg-white/10 flex-1"></div>
            </div>

            {/* INDIVIDUAL SUBJECTS GRID */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {availableSubjects.map((sub) => {
                const stats = subjectStats[sub.id] || { count: 0, dueCount: 0, avgR: 1.0 };
                const hasDue = stats.dueCount > 0;
                return (
                  <div
                    key={sub.id}
                    className="glass-card p-8 rounded-[2.5rem] border border-white/5 hover:border-primary/40 relative overflow-hidden flex flex-col justify-between group transition-all hover:-translate-y-1.5 hover:shadow-2xl"
                  >
                    <div className="absolute top-0 right-0 w-32 h-32 bg-primary/5 rounded-full -translate-y-16 translate-x-16 blur-3xl group-hover:bg-primary/20 transition-all pointer-events-none"></div>

                    <div className="space-y-4 relative z-10 mb-6">
                      <div className="flex justify-between items-start">
                        <div className="p-3 bg-white/5 rounded-2xl text-primary group-hover:bg-primary/20 transition-colors">
                          <GraduationCap size={24} />
                        </div>
                        {hasDue ? (
                          <span className="px-3 py-1 rounded-full text-[9px] font-black uppercase tracking-wider bg-primary/20 text-primary border border-primary/30 flex items-center gap-1.5 animate-pulse">
                            <Zap size={10} /> {stats.dueCount} Due Now
                          </span>
                        ) : (
                          <span className="px-3 py-1 rounded-full text-[9px] font-bold uppercase tracking-wider bg-white/5 text-slate-400 border border-white/5">
                            {stats.count} Cards
                          </span>
                        )}
                      </div>

                      <div>
                        <h3 className="text-2xl font-black text-white group-hover:text-primary transition-colors tracking-tight mb-2">
                          {sub.name}
                        </h3>
                        <p className="text-xs text-slate-400 line-clamp-2 leading-relaxed">
                          {sub.description || 'Spaced repetition domain for conceptual mastery.'}
                        </p>
                      </div>

                      <div className="space-y-2 pt-2">
                        <div className="flex justify-between items-center text-xs">
                          <span className="text-slate-400 text-[10px] font-bold uppercase tracking-wider">Retention Health</span>
                          <span className={`font-mono font-bold text-xs ${stats.avgR >= 0.85 ? 'text-success' : stats.avgR >= 0.5 ? 'text-warning' : 'text-destructive'}`}>
                            {(stats.avgR * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                          <div 
                            className="h-full bg-primary transition-all duration-1000" 
                            style={{ width: `${stats.avgR * 100}%` }}
                          ></div>
                        </div>
                      </div>
                    </div>

                    {/* Single-Subject Launch Actions */}
                    <div className="flex flex-col gap-2.5 relative z-10 pt-4 border-t border-white/5">
                      <button
                        onClick={() => handleSelectSubject(sub.id, false)}
                        className="w-full py-3.5 bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 text-white rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-indigo-500/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center justify-center gap-2"
                      >
                        <Play size={14} className="fill-current" /> Study This Subject
                      </button>
                      <button
                        onClick={() => handleSelectSubject(sub.id, true)}
                        className="w-full py-2.5 bg-amber-500/10 hover:bg-amber-500/20 text-amber-400 hover:text-amber-300 rounded-xl font-bold text-[10px] uppercase tracking-wider border border-amber-500/20 transition-all flex items-center justify-center gap-1.5"
                        title="Prioritize cards with lowest memory retention"
                      >
                        <Zap size={12} /> Logic Blitz (Cram)
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    );
  }

  // ==========================================
  // VIEW 2: LOADING QUEUE FOR CHOSEN SUBJECT / ALL
  // ==========================================
  if (loadingQueue) {
    return (
      <div className="flex h-[80vh] items-center justify-center bg-background">
         <div className="flex flex-col items-center gap-4">
            <Loader2 className="animate-spin text-primary" size={64} />
            <p className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-500">
              Loading {isExamMode ? 'Exam Queue' : 'Study Queue'} for {activeSubjectName}...
            </p>
         </div>
      </div>
    );
  }

  // ==========================================
  // VIEW 3: EMPTY / FINISHED SESSION
  // ==========================================
  if (dueConcepts.length === 0 || phase === 'finished') {
    return (
      <div className="p-8 max-w-4xl w-full mx-auto flex flex-col justify-center min-h-[80vh] text-center text-white animate-in fade-in duration-500">
        <motion.div 
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="glass-card p-12 md:p-16 rounded-[4rem] border border-white/5 shadow-2xl relative overflow-hidden"
        >
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-success/50 to-transparent"></div>
          <CheckCircle size={90} className="text-success mx-auto mb-8" />
          <span className="text-xs font-black uppercase tracking-[0.3em] text-primary block mb-2">
            {selectedSubjectId === 'all' ? 'Global Review Complete' : `Subject: ${activeSubjectName}`}
          </span>
          <h1 className="text-4xl md:text-5xl font-black mb-4 tracking-tighter text-white">Logic Cleared!</h1>
          <p className="text-slate-400 text-lg mb-10 max-w-md mx-auto leading-relaxed font-medium">
            {selectedSubjectId === 'all' 
              ? 'All scheduled logic reviews across all your subjects are completed and memory pathways consolidated.'
              : <>All scheduled logic reviews for <strong className="text-white font-bold">{activeSubjectName}</strong> are completed and memory pathways updated.</>}
          </p>
          <div className="flex flex-wrap gap-4 justify-center">
            <button 
              onClick={() => fetchQueueForSubject(selectedSubjectId, false, true)}
              className="bg-primary text-primary-foreground px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest shadow-xl shadow-primary/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-2"
            >
              <RefreshCw size={16} /> Practice All Cards Again
            </button>
            <button 
              onClick={handleSwitchSubject}
              className="glass px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-white/10 transition-all text-white border border-white/10 flex items-center gap-2 hover:scale-105 active:scale-95"
            >
              <ArrowLeft size={16} /> Choose Another Subject / Mode
            </button>
            <Link to="/analytics" className="glass px-8 py-4 rounded-2xl font-black text-xs uppercase tracking-widest hover:bg-white/10 transition-all text-slate-300 border border-white/5 flex items-center gap-2">
              <Award size={16} /> Metrics
            </Link>
          </div>
        </motion.div>
      </div>
    );
  }

  // ==========================================
  // VIEW 4: ACTIVE STUDY SESSION (ALL OR SINGLE SUBJECT)
  // ==========================================
  return (
    <div className={`p-4 md:p-12 max-w-[1600px] w-full mx-auto flex flex-col min-h-screen text-white ${isExamMode ? 'selection:bg-amber-500/30' : 'selection:bg-primary/30'}`}>
      {/* Header & Progress */}
      <div className="mb-10">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-6">
          <div className="flex items-center gap-4">
            <div className={`p-4 rounded-3xl border ${isExamMode ? 'bg-amber-500/20 border-amber-500/20' : 'bg-primary/20 border-primary/20'}`}>
              {selectedSubjectId === 'all' ? <Globe className="text-primary" size={28} /> : isExamMode ? <Zap className="text-amber-500" size={28} /> : <Code2 className="text-primary" size={28} />}
            </div>
            <div>
              <div className="flex items-center gap-3 mb-1">
                <h1 className="text-2xl md:text-3xl font-black tracking-tight">{activeSubjectName}</h1>
                <button
                  onClick={handleSwitchSubject}
                  className="px-3 py-1 bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white rounded-lg text-[9px] font-bold uppercase tracking-wider border border-white/5 transition-all flex items-center gap-1"
                  title="Switch to another subject or global review"
                >
                  <ArrowLeft size={10} /> Switch Mode
                </button>
              </div>
              <p className={`text-[10px] uppercase tracking-[0.3em] font-black flex items-center gap-2 ${isExamMode ? 'text-amber-500' : 'text-slate-400'}`}>
                {isExamMode ? <Sparkles size={10} /> : <Zap size={10} className="text-primary" />} 
                {selectedSubjectId === 'all' ? 'Global Full-Spectrum Cognitive Flow' : isExamMode ? 'Single-Subject Exam Blitz' : 'Single-Subject Active Study Session'}
              </p>
            </div>
          </div>

          <div className="flex items-end gap-8">
             <div className="flex flex-col items-end">
                <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Latency</span>
                <div className="flex items-center gap-2 text-primary font-mono font-black text-lg">
                   <Timer size={16} /> {cardTimer}s
                </div>
             </div>
             <div className="flex flex-col items-end">
                <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest mb-1">Queue</span>
                <p className="text-lg font-black text-white">{currentIndex + 1} <span className="opacity-30">/ {dueConcepts.length}</span></p>
             </div>
          </div>
        </div>
        <div className="h-1.5 w-full bg-white/[0.03] rounded-full overflow-hidden">
          <motion.div 
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            className={`h-full ${isExamMode ? 'bg-gradient-to-r from-amber-500 to-orange-500' : 'bg-gradient-to-r from-primary via-purple-500 to-accent'}`}
          ></motion.div>
        </div>
      </div>

      <div className="flex-1 flex flex-col gap-10">
        {/* Question Area */}
        <div className={`glass-card p-10 md:p-14 rounded-[3rem] border border-white/5 min-h-[200px] flex items-center justify-center text-center relative transition-all duration-700 ${phase !== 'question' ? (isExamMode ? 'bg-amber-500/[0.03] border-amber-500/20' : 'bg-primary/[0.03] border-primary/20') : ''}`}>
          <div className="absolute top-8 left-8 flex items-center gap-2 opacity-30">
            {isExamMode ? <Trophy size={22} className="text-amber-500" /> : <MessageSquare size={22} />}
            <span className="text-[9px] font-black uppercase tracking-[0.3em]">{isExamMode ? 'Exam Challenge' : 'Flashcard Target'}</span>
          </div>
          
          {/* Card Subject Badge if studying all subjects */}
          {selectedSubjectId === 'all' && currentCard?.subject_name && (
            <div className="absolute top-8 right-8 flex items-center gap-2 px-3 py-1 rounded-xl bg-white/5 border border-white/10 text-primary text-[10px] font-black uppercase tracking-wider">
              <Layers size={12} /> {currentCard.subject_name}
            </div>
          )}

          <div className="flex flex-col gap-2 max-w-4xl mx-auto">
            <span className={`text-[9px] font-black uppercase tracking-[0.5em] mb-2 opacity-60 ${isExamMode ? 'text-amber-500' : 'text-primary'}`}>
              {currentCard?.concept_title || 'Identity Pending'}
            </span>
            <h2 className="text-2xl md:text-4xl font-black leading-tight tracking-tight text-white">{displayFront}</h2>
          </div>
        </div>

        {/* Interaction Area */}
        {phase === 'question' ? (
          <div className="flex flex-col gap-8 animate-in fade-in slide-in-from-bottom-6 duration-700">
            <div className={`grid grid-cols-1 ${isCodeSubject ? 'xl:grid-cols-2' : ''} gap-8`}>
              {/* Text Input */}
              <div className="relative group">
                <div className="absolute top-6 left-8 z-10 px-3 py-1 bg-black/40 rounded-lg border border-white/5 text-[9px] font-black uppercase tracking-widest text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity">
                   Memory Buffer
                </div>
                <textarea
                  autoFocus
                  className="w-full bg-white/[0.02] border border-white/5 rounded-[2.5rem] px-8 md:px-10 py-10 md:py-12 text-white focus:ring-4 focus:ring-primary/5 outline-none min-h-[360px] resize-none text-lg md:text-xl leading-relaxed shadow-inner placeholder:text-slate-700 transition-all hover:bg-white/[0.04] scrollbar-none"
                  placeholder={isCodeSubject ? "Briefly explain the underlying logic of your implementation..." : "Recall the synaptic details and manifest them here..."}
                  value={typedAnswer}
                  onChange={(e) => setTypedAnswer(e.target.value)}
                ></textarea>
                <div className="absolute bottom-8 right-10 text-[9px] text-slate-700 font-black uppercase tracking-[0.2em] hidden md:block">
                  Ctrl + Enter to submit
                </div>
              </div>

              {/* Code Sandbox */}
              {isCodeSubject && (
                <div className="h-[450px] xl:h-auto animate-in zoom-in-95 duration-1000">
                   <CodeEditor 
                     code={codeSnippet} 
                     language={currentCard.subject_name?.toLowerCase().includes('javascript') ? 'javascript' : 'cpp'} 
                     onChange={(val) => setCodeSnippet(val)}
                   />
                </div>
              )}
            </div>

            <div className="flex flex-col sm:flex-row gap-4 max-w-2xl mx-auto w-full">
              <button 
                onClick={handleSkip}
                className="flex-1 py-4 md:py-5 rounded-2xl glass hover:bg-destructive/10 hover:text-destructive hover:border-destructive/30 text-slate-400 transition-all font-black text-xs uppercase tracking-[0.2em] border border-white/5 group order-2 sm:order-1"
              >
                <FastForward size={18} className="mx-auto mb-1 group-hover:translate-x-1 transition-transform" /> Skip Card
              </button>
              <button 
                onClick={handleAiGrade}
                disabled={!typedAnswer.trim() && !codeSnippet.trim()}
                className={`flex-[3] py-4 md:py-5 rounded-2xl text-lg md:text-xl font-black tracking-tight hover:opacity-90 transition-all flex items-center justify-center gap-3 shadow-2xl disabled:opacity-30 order-1 sm:order-2 ${isExamMode ? 'bg-amber-500 text-black shadow-amber-500/20' : 'bg-primary text-primary-foreground shadow-primary/20'}`}
              >
                Sync Knowledge <Bot size={24} />
              </button>
            </div>
          </div>
        ) : (
          <div className="space-y-10 animate-in fade-in slide-in-from-bottom-10 duration-1000">
            {/* AI Grading Section */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div className="glass-card p-8 md:p-10 rounded-[3rem] border-l-4 border-l-primary/50 relative overflow-hidden group">
                  <div className="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-[60px] group-hover:bg-primary/20 transition-all"></div>
                  <h3 className="text-[10px] uppercase font-black text-primary tracking-[0.3em] mb-4 flex items-center gap-3 relative z-10">
                    <Bot size={18} /> Neural Audit Feedback
                  </h3>
                  {isAiLoading ? (
                    <div className="flex items-center gap-4 text-slate-400 p-6 font-bold uppercase tracking-widest text-[10px]">
                      <Loader2 className="animate-spin" size={20} /> Analyzing synaptic logic with Gemini...
                    </div>
                  ) : (
                    <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed relative z-10">
                      <ReactMarkdown>{aiEvaluation?.feedback_markdown}</ReactMarkdown>
                    </div>
                  )}
                </div>

                {aiEvaluation?.follow_up_question && (
                  <div className="glass-card p-8 md:p-10 rounded-[3rem] border-l-4 border-l-accent/50 bg-accent/[0.02] transition-all hover:bg-accent/[0.05]">
                    <h3 className="text-[10px] uppercase font-black text-accent tracking-[0.3em] mb-3 flex items-center gap-3">
                      <Zap size={18} /> Socratic Follow-up
                    </h3>
                    <p className="text-lg font-black mb-4 tracking-tight text-white leading-tight">{aiEvaluation.follow_up_question}</p>
                    <input 
                      type="text"
                      className="w-full bg-white/[0.02] border border-white/10 rounded-2xl px-6 py-3.5 text-white focus:ring-2 focus:ring-accent outline-none text-sm transition-all focus:bg-black/40"
                      placeholder="Input response to reinforce this synapse..."
                      value={followUpAnswer}
                      onChange={e => setFollowUpAnswer(e.target.value)}
                    />
                  </div>
                )}
              </div>

              <div className="space-y-6">
                <div className="glass-card p-8 md:p-10 rounded-[3rem] border border-white/5">
                  <h3 className="text-[10px] uppercase font-black text-success tracking-[0.3em] mb-4 flex items-center gap-3">
                     <CheckCircle size={18} /> Target Recall / Answer
                  </h3>
                  <div className="prose prose-invert prose-sm max-w-none text-slate-300 leading-relaxed max-h-[360px] overflow-y-auto pr-4 scrollbar-thin scrollbar-thumb-white/10">
                    <ReactMarkdown>{displayBack}</ReactMarkdown>
                  </div>
                </div>
                
                <div className="glass-card p-8 md:p-10 rounded-[3rem] bg-black/40 border border-white/5">
                  <h3 className="text-[10px] uppercase font-black text-slate-500 tracking-[0.3em] mb-4">Your Manifested Record</h3>
                  <div className="text-sm italic text-slate-300 leading-relaxed max-h-[180px] overflow-y-auto scrollbar-thin">
                    {codeSnippet && (
                      <div className="mb-4 rounded-2xl overflow-hidden border border-white/5 bg-[#0d0d0d]">
                         <div className="px-4 py-1.5 bg-white/[0.02] border-b border-white/5 text-[8px] font-black text-slate-500 uppercase tracking-widest">Submitted Code</div>
                         <pre className="p-4 font-mono text-[11px] leading-relaxed text-emerald-400 overflow-x-auto">
                           {codeSnippet}
                         </pre>
                      </div>
                    )}
                    <p className="line-clamp-6 leading-relaxed">"{typedAnswer}"</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Grading Buttons */}
            <div className="flex flex-col gap-6 pt-6 border-t border-white/5">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <h3 className="text-xl font-black tracking-tight text-white">Manual Cognitive Assessment</h3>
                {!isAiLoading && (
                  <div className="px-4 py-2 rounded-full bg-primary/10 border border-primary/20 flex items-center gap-2">
                    <Bot size={14} className="text-primary" />
                    <span className="text-[9px] font-black text-primary uppercase tracking-[0.2em]">
                      AI Recommendation: {currentCard.algorithm === 'sm2' ? aiEvaluation?.sm2_score : aiEvaluation?.fsrs_score}
                    </span>
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 md:gap-6">
                {[
                  { r: 1, l: 'Again', c: 'hover:bg-destructive/20 hover:text-destructive hover:border-destructive/40', desc: 'Blackout', hotkey: '1' },
                  { r: 2, l: 'Hard', c: 'hover:bg-warning/20 hover:text-warning hover:border-warning/40', desc: 'Neural Friction', hotkey: '2' },
                  { r: 3, l: 'Good', c: 'hover:bg-primary/20 hover:text-primary hover:border-primary/40', desc: 'Synapse Clear', hotkey: '3' },
                  { r: 4, l: 'Easy', c: 'hover:bg-success/20 hover:text-success hover:border-success/40', desc: 'Absolute Recall', hotkey: '4' }
                ].map(btn => (
                  <button
                    key={btn.r}
                    onClick={() => submitFinalGrade(btn.r)}
                    disabled={isAiLoading}
                    className={`flex flex-col items-center gap-1.5 py-6 md:py-8 rounded-[2rem] glass transition-all border-white/5 group ${btn.c} disabled:opacity-30`}
                  >
                    <span className="text-[9px] font-black opacity-30 group-hover:opacity-100 transition-opacity">KEY {btn.hotkey}</span>
                    <span className="text-2xl md:text-3xl font-black tracking-tighter">{btn.l}</span>
                    <span className="text-[9px] font-bold uppercase tracking-widest opacity-40">{btn.desc}</span>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="mt-auto py-8 flex items-center justify-between border-t border-white/5">
            <button 
               onClick={handleSwitchSubject}
               className="text-slate-400 hover:text-white flex items-center gap-2 transition-all px-4 py-2 rounded-xl text-[10px] font-black uppercase tracking-wider hover:bg-white/5"
            >
              <ArrowLeft size={14} /> Change Subject / Mode
            </button>
            <button 
               onClick={() => setPhase('finished')}
               className="text-slate-500 hover:text-destructive flex items-center gap-2 transition-all glass px-6 py-2.5 rounded-xl text-[10px] font-black uppercase tracking-[0.2em] hover:border-destructive/30"
            >
              <Flag size={14} /> End Session
            </button>
        </div>
      </div>
    </div>
  );
};

export default Study;
