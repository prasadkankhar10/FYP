import React, { useState, useContext, useEffect } from 'react';
import { AuthContext } from '../context/AuthContext';
import { Bot, Save, Loader2, Sparkles, BookOpen } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import api from '../api';

const AiTutor = () => {
  const { user } = useContext(AuthContext);
  const [bio, setBio] = useState('');
  const [savingBio, setSavingBio] = useState(false);
  const [bioSaved, setBioSaved] = useState(false);
  
  const [advice, setAdvice] = useState('');
  const [loadingAdvice, setLoadingAdvice] = useState(false);

  const [pdfText, setPdfText] = useState('');
  const [selectedSubject, setSelectedSubject] = useState('');
  const [subjects, setSubjects] = useState([]);
  const [generatingC, setGeneratingC] = useState(false);
  
  const [previewCards, setPreviewCards] = useState([]);
  const [savingCards, setSavingCards] = useState(false);
  
  useEffect(() => {
    // Load current bio from user context or fetch it
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
      setBioSaved(true);
      setTimeout(() => setBioSaved(false), 3000);
    } catch (err) {
      alert("Failed to save profile.");
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
      alert("Failed to get AI advice. Ensure backend is running and Groq API key is valid.");
    } finally {
      setLoadingAdvice(false);
    }
  };

  const handleGenerateFlashcards = async () => {
    if (!selectedSubject || !pdfText) {
      alert("Please select a subject and paste some text.");
      return;
    }
    setGeneratingC(true);
    try {
      const res = await api.post('/ai/generate-flashcards', {
        subject_id: parseInt(selectedSubject),
        source_text: pdfText
      });
      setPreviewCards(res.data.cards);
    } catch (err) {
      alert("AI Generation failed. Try a smaller text block.");
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
      alert(`Success! Saved ${res.data.concepts_created} new concepts to your deck.`);
      setPreviewCards([]);
      setPdfText('');
    } catch (err) {
      alert("Failed to save flashcards.");
    } finally {
      setSavingCards(false);
    }
  };

  const handleConnectGraph = async () => {
    try {
      const res = await api.post('/ai/connect-concepts');
      alert(`Optimization complete! Made ${res.data.connections_made} relational FYP connections.`);
    } catch (err) {
      alert("Failed to connect graph.");
    }
  };

  return (
    <div className="p-8 max-w-6xl w-full">
      <div className="flex items-center gap-4 mb-8">
        <Bot size={40} className="text-blue-400" />
        <h1 className="text-4xl font-bold">AI Academic Tutor</h1>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left Column: Context Setup */}
        <div className="flex flex-col gap-8">
          <div className="glass p-8 rounded-3xl border border-white/10">
            <div className="flex justify-between items-center mb-2">
               <h2 className="text-2xl font-bold">1. Your Profile & Goals</h2>
               <button
                 onClick={() => {
                   const promptText = "I am using a new adaptive flashcard app that uses advanced machine learning algorithms (FSRS) to orchestrate my study schedule. Based on everything you know about my educational background, my primary learning goals, and what subjects I generally struggle with, please write a concise, one-paragraph academic profile describing me. This will be fed to an AI Tutor to help generate a curated curriculum for me.";
                   navigator.clipboard.writeText(promptText);
                   alert("Prompt copied to clipboard! Paste it into your external AI.");
                 }}
                 className="text-xs bg-slate-800 hover:bg-slate-700 text-slate-300 py-1.5 px-3 rounded-lg border border-white/10 transition-colors flex items-center gap-1.5"
               >
                 <Bot size={14} className="text-blue-400" /> Copy From Other AI
               </button>
            </div>
            <p className="text-slate-400 mb-6 text-sm">Tell the AI about yourself to get personalized advice, or use the button above to ask your favorite AI to write it for you.</p>
            
            <textarea
              className="w-full bg-slate-900/50 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 h-32 resize-none mb-4"
              placeholder="e.g. I am a 3rd Year Biology student aiming to master genetics. I struggle with memorizing long protein sequences..."
              value={bio}
              onChange={(e) => setBio(e.target.value)}
            ></textarea>
            
            <div className="flex justify-end">
              <button 
                onClick={handleSaveBio}
                disabled={savingBio}
                className="bg-white/10 hover:bg-white/20 px-6 py-2.5 rounded-xl transition-colors flex items-center gap-2"
              >
                {savingBio ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                {bioSaved ? "Saved!" : "Save Profile"}
              </button>
            </div>
          </div>

          <div className="glass p-8 rounded-3xl border border-blue-500/30 bg-blue-900/10 relative overflow-hidden">
             {/* Fancy background glow */}
             <div className="absolute -top-24 -right-24 w-48 h-48 bg-blue-500/20 blur-3xl rounded-full"></div>
             
             <h2 className="text-2xl font-bold mb-2 text-blue-300 flex items-center gap-2">
                <Sparkles size={24} /> Auto-Flashcard Generator
             </h2>
             <p className="text-slate-400 mb-6 text-sm">Paste your lecture notes. Llama 3 will extract the highest-yield facts and instantly convert them into flashcards!</p>
             
             <select 
               className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3 text-white mb-4 focus:ring-2 focus:ring-blue-500"
               value={selectedSubject}
               onChange={(e) => setSelectedSubject(e.target.value)}
             >
                <option value="">-- Select target Subject --</option>
                {subjects.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
             </select>

             <textarea
              className="w-full bg-slate-900/80 border border-white/10 rounded-xl px-4 py-3 text-white focus:ring-2 focus:ring-blue-500 h-40 resize-none mb-4"
              placeholder="Paste Wikipedia article, lecture transcript, or study guide text here..."
              value={pdfText}
              onChange={(e) => setPdfText(e.target.value)}
              disabled={previewCards.length > 0}
             ></textarea>

             {previewCards.length > 0 ? (
               <div className="flex flex-col gap-4">
                 <div className="bg-slate-900/50 rounded-xl p-4 max-h-48 overflow-y-auto mb-2 border border-white/10">
                   <p className="text-sm text-slate-300 font-bold mb-2">Generated Preview:</p>
                   {previewCards.map((card, idx) => (
                     <div key={idx} className="mb-3 border-b border-white/10 pb-2">
                       <p className="font-semibold text-white text-sm">Q: {card.title}</p>
                       <p className="text-slate-400 text-xs mt-1">A: {card.content}</p>
                     </div>
                   ))}
                 </div>
                 <div className="flex gap-3">
                   <button 
                     onClick={() => setPreviewCards([])}
                     disabled={savingCards}
                     className="flex-1 py-3 rounded-xl bg-slate-800 hover:bg-slate-700 transition-colors font-bold border border-white/10"
                   >
                     Discard / Retry
                   </button>
                   <button 
                     onClick={handleSaveFlashcards}
                     disabled={savingCards}
                     className="flex-1 py-3 rounded-xl bg-green-600 hover:bg-green-500 transition-colors font-bold shadow-lg shadow-green-500/20 flex justify-center items-center gap-2"
                   >
                     {savingCards ? <Loader2 className="animate-spin" size={18} /> : <Save size={18} />}
                     Save to Deck
                   </button>
                 </div>
               </div>
             ) : (
               <button 
                 onClick={handleGenerateFlashcards}
                 disabled={generatingC || !selectedSubject || !pdfText}
                 className="w-full py-3 rounded-xl bg-blue-600 hover:bg-blue-500 transition-colors font-bold disabled:opacity-50 flex items-center justify-center gap-2"
               >
                 {generatingC ? <Loader2 className="animate-spin" size={18} /> : <BookOpen size={18} />}
                 Generate Flashcards
               </button>
             )}
          </div>
        </div>

        {/* Right Column: AI Output */}
        <div className="flex flex-col gap-6">
          <div className="glass p-8 rounded-3xl border border-white/10 shadow-2xl flex-1 flex flex-col">
            <div className="flex justify-between items-center mb-6 border-b border-white/10 pb-4">
              <h2 className="text-2xl font-bold">2. Tutor Advice</h2>
              <button 
                onClick={fetchAdvice}
                disabled={loadingAdvice}
                className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded-lg font-medium transition-colors flex items-center gap-2 disabled:opacity-50"
              >
                {loadingAdvice ? <Loader2 className="animate-spin" size={16} /> : <Bot size={16} />}
                Ask Tutor
              </button>
            </div>
            
            <div className="flex-1 bg-slate-900/50 rounded-2xl p-6 overflow-y-auto min-h-[300px]">
              {advice ? (
                <div className="prose prose-invert prose-indigo max-w-none text-slate-300">
                   <ReactMarkdown>{advice}</ReactMarkdown>
                </div>
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-slate-500 text-center">
                   <Bot size={48} className="mb-4 opacity-50" />
                   <p>Click "Ask Tutor" to generate your custom academic curriculum based on your profile.</p>
                </div>
              )}
            </div>
          </div>

          {/* Multi-Concept FYP Feature trigger */}
          <div className="glass p-6 rounded-2xl border-l-4 border-l-purple-500 flex justify-between items-center">
            <div>
              <h3 className="font-bold text-lg text-purple-300">Run FYP Graph Optimization</h3>
              <p className="text-sm text-slate-400 mt-1 max-w-sm">Use AI to scan your entire deck and auto-connect Prerequisite relationships for the Multi-FSRS algorithm.</p>
            </div>
            <button onClick={handleConnectGraph} className="bg-purple-600 hover:bg-purple-500 px-4 py-2 rounded-xl font-bold whitespace-nowrap transition-colors">
              Optimize Graph
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AiTutor;
