import React, { useState } from "react";
import Editor from "@monaco-editor/react";
import { Copy, Check, Code2 } from "lucide-react";

const LANGUAGES = [
  { id: "cpp", name: "C++" },
  { id: "javascript", name: "JavaScript" },
  { id: "python", name: "Python" },
  { id: "html", name: "HTML/CSS" },
];

const CodeEditor = ({ code, language = "cpp", onChange }) => {
  const [copied, setCopied] = useState(false);
  const [selectedLang, setSelectedLang] = useState(language);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-[500px] rounded-3xl overflow-hidden border border-white/5 bg-[#0d0d0d] shadow-2xl animate-in zoom-in-95 duration-500">
      {/* IDE Header */}
      <div className="flex flex-col sm:flex-row items-center justify-between px-6 py-3 bg-white/[0.02] border-b border-white/5 gap-4">
        <div className="flex items-center gap-4">
          <div className="flex gap-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-[#ff5f56]"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-[#ffbd2e]"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-[#27c93f]"></div>
          </div>
          
          <div className="h-4 w-px bg-white/10 mx-2 hidden sm:block"></div>
          
          <div className="flex items-center gap-2 bg-white/5 px-3 py-1 rounded-lg border border-white/5 group cursor-pointer hover:bg-white/10 transition-all">
            <Code2 size={12} className="text-primary" />
            <select 
              value={selectedLang} 
              onChange={(e) => setSelectedLang(e.target.value)}
              className="bg-transparent border-none text-[10px] font-black uppercase tracking-widest outline-none cursor-pointer appearance-none pr-4"
            >
              {LANGUAGES.map(l => <option key={l.id} value={l.id} className="bg-slate-950 text-white">{l.name}</option>)}
            </select>
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={handleCopy}
            className="p-2 hover:bg-white/5 rounded-xl text-slate-500 hover:text-white transition-all border border-transparent hover:border-white/10"
            title="Copy Code"
          >
            {copied ? <Check size={16} className="text-success" /> : <Copy size={16} />}
          </button>
        </div>
      </div>

      {/* Main Layout: Editor Only */}
      <div className="flex-grow flex flex-col relative min-h-[300px]">
        <Editor
          height="100%"
          defaultLanguage={selectedLang}
          language={selectedLang}
          theme="github-dark"
          value={code}
          onChange={onChange}
          beforeMount={(monaco) => {
            monaco.editor.defineTheme("github-dark", {
              base: "vs-dark",
              inherit: true,
              rules: [
                { token: "keyword", foreground: "F97583" },
                { token: "string", foreground: "9ECBFF" },
                { token: "comment", foreground: "6A737D", fontStyle: "italic" },
                { token: "type", foreground: "B392F0" },
                { token: "class", foreground: "B392F0" },
                { token: "number", foreground: "79B8FF" },
                { token: "function", foreground: "B392F0" },
                { token: "variable", foreground: "E1E4E8" },
                { token: "constant", foreground: "79B8FF" },
              ],
              colors: {
                "editor.background": "#24292e",
                "editor.foreground": "#e1e4e8",
                "editorLineNumber.foreground": "#444d56",
                "editor.selectionBackground": "#3392FF44",
                "editor.inactiveSelectionBackground": "#3392FF22",
                "editorIndentGuide.background": "#444d56",
                "editorIndentGuide.activeBackground": "#e1e4e8",
              }
            });
          }}
          options={{
            minimap: { enabled: false },
            fontSize: 13,
            lineNumbers: "on",
            roundedSelection: true,
            scrollBeyondLastLine: false,
            readOnly: false,
            automaticLayout: true,
            padding: { top: 20, bottom: 20 },
            fontFamily: "\"Fira Code\", \"JetBrains Mono\", monospace",
            cursorBlinking: "smooth",
            cursorSmoothCaretAnimation: "on",
            smoothScrolling: true,
          }}
        />
      </div>
    </div>
  );
};

export default CodeEditor;
