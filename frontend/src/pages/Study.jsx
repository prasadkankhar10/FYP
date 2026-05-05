import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle2, BookOpen, Bot, FastForward, Flag } from 'lucide-react';
import api from '../api';
import { Link } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';

const Study = () => {
  const [dueConcepts, setDueConcepts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  
  const [typedAnswer, setTypedAnswer] = useState('');
  
  // Tracking
  const [sessionReport, setSessionReport] = useState([]);
  const [isReportView, setIsReportView] = useState(false);

  useEffect(() => {
    const fetchDue = async () => {
      try {
        const res = await api.get('/reviews/due');
        setDueConcepts(res.data);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    fetchDue();
  }, []);

  const processAIBackground = async (concept, answerText, reportId) => {
    let aiScoreObj;
    let fallbackFailed = false;

    try {
      const res = await api.post('/ai/evaluate-answer', {
        concept_id: concept.concept_id,
        typed_answer: answerText
      });
      aiScoreObj = res.data;
    } catch {
      fallbackFailed = true;
    }

    // Determine the numerical score
    let qualityScore = fallbackFailed ? 1 : 0;
    if (!fallbackFailed) {
      if (concept.algorithm === 'sm2') qualityScore = aiScoreObj.sm2_score;
      else qualityScore = aiScoreObj.fsrs_score;
    }

    let was_correct = false;
    if (concept.algorithm === 'sm2' && qualityScore >= 3) was_correct = true;
    if (concept.algorithm !== 'sm2' && qualityScore > 1) was_correct = true;

    // Send the score silently to the database
    try {
      await api.post('/reviews/submit', {
        concept_id: concept.concept_id,
        quality_score: qualityScore,
        was_correct: was_correct,
      });
    } catch (e) {
      console.error(e);
    }

    // Update the visual report status map
    setSessionReport(prev => prev.map(item => {
      if (item.id === reportId) {
        return {
          ...item,
          status: 'done',
          feedback_markdown: fallbackFailed ? "Failed to get AI grading due to server error." : aiScoreObj.feedback_markdown,
          numeric_score: qualityScore
        };
      }
      return item;
    }));
  };

  const handleSubmitAsync = () => {
    if (!typedAnswer.trim()) {
      alert("Please type your answer from memory or skip.");
      return;
    }
    const currentConcept = dueConcepts[currentIndex];
    const reportId = Date.now();
    
    // Create loading placeholder
    const newReportItem = {
      id: reportId,
      concept_title: currentConcept.concept_title,
      true_answer: currentConcept.concept_content,
      typed_answer: typedAnswer,
      algorithm: currentConcept.algorithm,
      status: 'loading'
    };
    setSessionReport(prev => [...prev, newReportItem]);

    // Fire & Forget
    processAIBackground(currentConcept, typedAnswer, reportId);
    
    setTypedAnswer('');
    setCurrentIndex(prev => prev + 1);
  };

  const handleSkip = async () => {
    const currentConcept = dueConcepts[currentIndex];
    const qualityScore = currentConcept.algorithm === 'sm2' ? 0 : 1; 

    // Instantly log a failure without hitting AI
    api.post('/reviews/submit', {
      concept_id: currentConcept.concept_id,
      quality_score: qualityScore,
      was_correct: false,
    }).catch(console.error);

    setSessionReport(prev => [...prev, {
      id: Date.now(),
      concept_title: currentConcept.concept_title,
      true_answer: currentConcept.concept_content,
      typed_answer: "(Skipped)",
      algorithm: currentConcept.algorithm,
      status: 'done',
      feedback_markdown: "**You skipped this question.** The database recorded a blackout / fail for this iteration.",
      numeric_score: qualityScore
    }]);

    setTypedAnswer('');
    setCurrentIndex(prev => prev + 1);
  };

  const toggleReportView = () => setIsReportView(true);

  if (loading) {
    return <div className="p-8 flex justify-center"><Loader2 className="animate-spin text-purple-400" size={48} /></div>;
  }

  if (dueConcepts.length === 0) {
    return (
      <div className="p-8 max-w-4xl w-full mx-auto mt-12 text-center">
        <div className="glass p-16 rounded-3xl inline-flex flex-col items-center">
          <CheckCircle2 size={80} className="text-green-400 mb-6" />
          <h1 className="text-4xl font-bold mb-4">No due concepts!</h1>
          <p className="text-slate-400 text-lg mb-8 max-w-md">You have no scheduled reviews for today.</p>
          <Link to="/subjects" className="bg-white/10 hover:bg-white/20 px-6 py-3 rounded-xl transition-colors font-medium">
            Browse Subjects
          </Link>
        </div>
      </div>
    );
  }

  // REPLACEMENT: Report End View
  if (isReportView || currentIndex >= dueConcepts.length) {
    return (
      <div className="p-8 max-w-5xl w-full mx-auto flex flex-col min-h-screen">
        <div className="mb-8 flex justify-between items-end">
           <div>
             <h1 className="text-4xl font-bold mb-2 flex items-center gap-3">
                <Bot className="text-purple-400" size={32} /> Session Report
             </h1>
             <p className="text-slate-400">Review the AI's detailed feedback on your memory retention.</p>
           </div>
           <Link to="/subjects" className="bg-white/10 hover:bg-white/20 px-6 py-3 rounded-xl transition-colors font-medium text-white flex items-center gap-2">
             Finish Session
           </Link>
        </div>

        {sessionReport.length === 0 ? (
          <div className="glass p-8 rounded-2xl text-center text-slate-400">No questions answered this session.</div>
        ) : (
          <div className="flex flex-col gap-8">
            {sessionReport.map((item, i) => (
              <div key={item.id} className="glass p-8 rounded-3xl border-l-4 border-l-purple-500 flex flex-col gap-4">
                
                <h2 className="text-2xl font-bold mb-2">Q{i + 1}: {item.concept_title}</h2>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 bg-slate-900/50 p-6 rounded-2xl border border-white/5">
                  <div>
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">Your Answer</h3>
                    <p className="text-slate-200 text-lg italic bg-black/20 p-4 rounded-xl border border-white/5">{item.typed_answer}</p>
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-slate-400 uppercase tracking-wider mb-2">True Answer</h3>
                    <div className="text-slate-200 text-base bg-black/20 p-4 rounded-xl border border-white/5 prose-invert prose-sm max-w-none max-h-48 overflow-y-auto">
                       <ReactMarkdown>{item.true_answer}</ReactMarkdown>
                    </div>
                  </div>
                </div>

                <div className="mt-2 text-left">
                  <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider mb-2 flex items-center gap-2">
                     <Bot size={16} /> AI Feedback Analysis
                  </h3>
                  {item.status === 'loading' ? (
                     <div className="flex items-center gap-3 text-slate-400 p-4 bg-blue-900/10 rounded-xl border border-blue-500/20">
                       <Loader2 className="animate-spin" size={20} /> AI is currently generating feedback for this answer...
                     </div>
                  ) : (
                     <div className="text-lg text-slate-200 bg-blue-900/10 p-6 rounded-xl border border-blue-500/20 prose prose-invert prose-blue max-w-none">
                        <ReactMarkdown>{item.feedback_markdown}</ReactMarkdown>
                     </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  const currentCard = dueConcepts[currentIndex];

  return (
    <div className="p-8 max-w-4xl w-full mx-auto flex flex-col min-h-[calc(100vh-4rem)]">
      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-3xl font-bold">Study Session</h1>
          <p className="text-slate-400 mt-1">Algorithm in use: <span className="uppercase text-purple-400 font-bold">{currentCard.algorithm}</span></p>
        </div>
        <div className="text-lg font-medium text-slate-300">
          Card {currentIndex + 1} of {dueConcepts.length}
        </div>
      </div>

      <div className="flex-1 flex flex-col justify-center gap-6">
        {/* Front of Card */}
        <div className="glass p-12 rounded-3xl min-h-[300px] flex items-center justify-center text-center relative border border-white/10 shadow-2xl">
          <BookOpen className="absolute top-6 left-6 text-slate-800" size={40} />
          <div>
            <h2 className="text-4xl font-bold leading-tight">{currentCard.concept_title}</h2>
          </div>
        </div>

        {/* Answer Input Actions */}
        <div className="w-full max-w-3xl mx-auto flex flex-col gap-4">
          <textarea
            className="w-full bg-slate-900/80 border border-white/10 rounded-2xl px-8 py-6 text-white focus:ring-2 focus:ring-purple-500 min-h-[180px] resize-none text-xl shadow-inner placeholder:text-slate-600"
            placeholder="Close your eyes, recall the information, and type your detailed answer here..."
            value={typedAnswer}
            onChange={(e) => setTypedAnswer(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && e.ctrlKey) handleSubmitAsync();
            }}
          ></textarea>

          <div className="flex gap-4 w-full">
            <button 
              onClick={handleSkip}
              className="flex-1 py-4 rounded-2xl bg-white/5 hover:bg-red-500/20 hover:text-red-300 hover:border-red-500/30 border border-white/10 text-slate-300 transition-all font-bold tracking-wide flex items-center justify-center gap-2"
            >
              <FastForward size={20} /> Skip (Blackout)
            </button>
            <button 
              onClick={handleSubmitAsync}
              disabled={!typedAnswer.trim()}
              className="flex-[2] py-4 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xl font-bold tracking-wide hover:opacity-90 transition-opacity flex items-center justify-center gap-2 shadow-lg shadow-indigo-500/20 disabled:opacity-50"
            >
              Submit Answer <Bot size={24} />
            </button>
          </div>
          <p className="text-center text-slate-500 text-sm mt-2">Press Ctrl + Enter to submit instantly.</p>
        </div>

        <div className="mt-8 text-center flex justify-center">
            <button 
               onClick={toggleReportView}
               className="text-slate-500 hover:text-white flex items-center gap-2 transition-colors border border-white/10 px-4 py-2 rounded-lg bg-black/20"
            >
              <Flag size={16} /> End Session Early
            </button>
        </div>
      </div>
    </div>
  );
};

export default Study;
