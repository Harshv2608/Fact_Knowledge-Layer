"use client";

import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, Upload, RefreshCw, FileText, Database, GitMerge, FileCheck2, Filter, Info, ShieldAlert, CheckCircle2, ChevronRight } from "lucide-react";

type Document = { id: number; filename: string; status: string; };
type Fact = { id: number; subject: string; predicate: string; raw_value: string; raw_unit: string; normalized_numeric_value: number; normalized_scale: string; normalized_currency: string; time_context: string; scope: string; geography: string; sign_convention_applied: string; evidence: string; };
type Relationship = { id: number; fact_a_id: number; fact_b_id: number; relationship_type: string; confidence: number; explanation: string; };

export default function Home() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [facts, setFacts] = useState<Fact[]>([]);
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [loading, setLoading] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeTab, setActiveTab] = useState("facts"); // "facts" or "relationships"

  const fetchData = async () => {
    try {
      const [docRes, factRes, relRes] = await Promise.all([
        fetch(`http://localhost:8000/api/documents/`),
        fetch(`http://localhost:8000/api/facts/`),
        fetch(`http://localhost:8000/api/relationships/`)
      ]);
      setDocuments(await docRes.json());
      setFacts(await factRes.json());
      setRelationships(await relRes.json());
    } catch (error) {
      console.error("Failed to fetch data:", error);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchData();
  }, []);

  const uploadFile = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    setLoading(true);
    try {
      const uploadPromises = Array.from(e.target.files).map(file => {
        const formData = new FormData();
        formData.append("file", file);
        return fetch("http://localhost:8000/api/documents/upload", {
          method: "POST",
          body: formData,
        });
      });
      
      await Promise.all(uploadPromises);
      fetchData();
      
      // Poll more aggressively initially, then slow down
      let pollCount = 0;
      const poll = setInterval(() => {
        pollCount++;
        fetchData();
        if (pollCount > 15) clearInterval(poll); // Stop after ~45s
      }, 3000);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const computeRelationships = async () => {
    setLoading(true);
    try {
      await fetch("http://localhost:8000/api/relationships/compute", { method: "POST" });
      await fetchData();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  // Filter facts based on search
  const filteredFacts = useMemo(() => {
    if (!searchQuery) return facts;
    const lowerQ = searchQuery.toLowerCase();
    return facts.filter((f: Fact) => 
      (f.subject && f.subject.toLowerCase().includes(lowerQ)) ||
      (f.predicate && f.predicate.toLowerCase().includes(lowerQ)) ||
      (f.raw_value && f.raw_value.toLowerCase().includes(lowerQ)) ||
      (f.normalized_numeric_value && String(f.normalized_numeric_value).includes(lowerQ))
    );
  }, [facts, searchQuery]);

  return (
    <div className="flex h-screen bg-neutral-50 text-neutral-900 font-sans overflow-hidden selection:bg-neutral-200 selection:text-neutral-900">
      
      {/* Sidebar */}
      <aside className="w-80 bg-white border-r border-neutral-200 shadow-sm flex flex-col z-10">
        <div className="p-6 border-b border-neutral-100 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-neutral-900 text-white p-2 rounded-lg shadow-sm">
              <Database size={20} />
            </div>
            <div>
              <h1 className="text-lg font-bold tracking-tight text-neutral-900 leading-none">Fact Layer</h1>
              <p className="text-[10px] text-neutral-500 font-medium tracking-widest uppercase mt-1">Superjoin Intern</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-5 space-y-8 custom-scrollbar">
          <section>
            <h2 className="text-[11px] font-bold text-neutral-400 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Upload size={14} /> Knowledge Ingestion
            </h2>
            <div className="relative group cursor-pointer">
              <div className="absolute inset-0 bg-neutral-50 rounded-xl border border-dashed border-neutral-300 transition-colors group-hover:border-neutral-500 group-hover:bg-neutral-100" />
              <input type="file" multiple onChange={uploadFile} className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10" accept=".pdf" />
              <div className="relative py-8 px-6 text-center pointer-events-none">
                <FileCheck2 className="mx-auto text-neutral-400 mb-3 group-hover:text-neutral-700 transition-colors" size={24} />
                <p className="text-sm font-semibold text-neutral-800">Upload PDF Source</p>
                <p className="text-xs text-neutral-500 mt-1">Extracts facts automatically</p>
              </div>
            </div>
          </section>

          <section>
            <div className="flex items-center justify-between mb-3">
              <h2 className="text-[11px] font-bold text-neutral-400 uppercase tracking-widest flex items-center gap-2">
                <FileText size={14} /> Sources
              </h2>
              <button onClick={fetchData} className="text-neutral-400 hover:text-neutral-800 transition-colors p-1 rounded hover:bg-neutral-100">
                <RefreshCw size={14} className={loading ? "animate-spin text-neutral-800" : ""} />
              </button>
            </div>
            <ul className="space-y-2">
              {documents.length === 0 ? (
                <li className="text-sm text-neutral-400 italic text-center p-4 bg-neutral-50 rounded-xl border border-neutral-100/50">No documents yet</li>
              ) : (
                documents.map((doc: Document) => (
                  <li key={doc.id} className="p-3 bg-white border border-neutral-200 rounded-xl shadow-sm hover:border-neutral-300 transition-colors">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium text-neutral-700 truncate w-3/4" title={doc.filename}>{doc.filename}</span>
                    </div>
                    <div className="flex items-center mt-2">
                      <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                        doc.status === 'EXTRACTED' ? 'bg-emerald-50 text-emerald-700 border border-emerald-100' :
                        doc.status === 'ERROR' ? 'bg-red-50 text-red-700 border border-red-100' :
                        'bg-amber-50 text-amber-700 border border-amber-100 animate-pulse'
                      }`}>
                        {doc.status}
                      </span>
                    </div>
                  </li>
                ))
              )}
            </ul>
          </section>
        </div>

        <div className="p-5 border-t border-neutral-200 bg-white mt-auto">
          <button 
            onClick={computeRelationships} 
            disabled={loading}
            className="w-full py-2.5 px-4 bg-neutral-900 hover:bg-neutral-800 text-white rounded-lg font-medium text-sm flex items-center justify-center gap-2 transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm focus:outline-none focus:ring-2 focus:ring-neutral-500 focus:ring-offset-2"
          >
            <GitMerge size={16} /> Compute Logic
          </button>
          <p className="text-[11px] text-center text-neutral-400 mt-3 font-medium">Finds corroborations & contradictions</p>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col bg-neutral-50 relative h-full overflow-hidden">
        
        {/* Header / Search */}
        <header className="h-16 bg-white border-b border-neutral-200 flex items-center justify-between px-8 z-10 shrink-0">
          <div className="flex space-x-6 h-full">
            <button 
              onClick={() => setActiveTab("facts")}
              className={`h-full border-b-2 font-medium text-sm transition-all px-1 ${activeTab === "facts" ? "border-neutral-900 text-neutral-900" : "border-transparent text-neutral-500 hover:text-neutral-800"}`}
            >
              Fact Directory <span className="ml-1 text-[10px] bg-neutral-100 text-neutral-600 px-1.5 py-0.5 rounded-full">{filteredFacts.length}</span>
            </button>
            <button 
              onClick={() => setActiveTab("relationships")}
              className={`h-full border-b-2 font-medium text-sm transition-all px-1 ${activeTab === "relationships" ? "border-neutral-900 text-neutral-900" : "border-transparent text-neutral-500 hover:text-neutral-800"}`}
            >
              Relationships <span className="ml-1 text-[10px] bg-neutral-100 text-neutral-600 px-1.5 py-0.5 rounded-full">{relationships.length}</span>
            </button>
          </div>

          <div className="relative w-72">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" size={16} />
            <input 
              type="text" 
              placeholder="Filter facts..." 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-9 pr-3 py-1.5 bg-neutral-100 border border-transparent rounded-md text-sm text-neutral-900 placeholder:text-neutral-400 focus:outline-none focus:bg-white focus:border-neutral-300 focus:ring-2 focus:ring-neutral-200 transition-all"
            />
          </div>
        </header>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-8 custom-scrollbar">
          
          <AnimatePresence mode="wait">
            {activeTab === "facts" ? (
              <motion.div 
                key="facts"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="grid gap-6 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4"
              >
                {filteredFacts.length === 0 ? (
                  <div className="col-span-full py-32 text-center text-neutral-400">
                    <Filter size={32} className="mx-auto mb-4 opacity-50" />
                    <p className="text-base font-medium text-neutral-600">No facts found</p>
                    <p className="text-sm mt-1">Upload a PDF or adjust your search.</p>
                  </div>
                ) : (
                  filteredFacts.map((fact: Fact) => (
                    <motion.div 
                      layout
                      key={fact.id} 
                      className="bg-white border border-neutral-200 rounded-xl p-5 shadow-[0_1px_2px_rgba(0,0,0,0.02)] hover:shadow-md transition-shadow flex flex-col"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <h3 className="font-semibold text-neutral-900 leading-tight">{fact.subject}</h3>
                        <span className="text-[10px] font-mono bg-neutral-100 text-neutral-500 px-1.5 py-0.5 rounded shrink-0 ml-2 border border-neutral-200/50">ID:{fact.id}</span>
                      </div>
                      
                      <div className="space-y-4 flex-1">
                        <div>
                          <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-1.5">Predicate</p>
                          <p className="text-sm text-neutral-800 bg-neutral-50 px-3 py-2 rounded-md border border-neutral-100 font-medium">{fact.predicate}</p>
                        </div>
                        
                        <div className="grid grid-cols-2 gap-3">
                          <div>
                            <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-1.5">Raw Extract</p>
                            <p className="text-sm font-semibold text-amber-800 bg-amber-50/50 px-2 py-1.5 rounded-md border border-amber-100/80">
                              {fact.raw_value} {fact.raw_unit}
                            </p>
                          </div>
                          <div>
                            <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-1.5">Normalized</p>
                            <p className="text-sm font-semibold text-emerald-800 bg-emerald-50/50 px-2 py-1.5 rounded-md border border-emerald-100/80 truncate" title={`${fact.normalized_numeric_value != null ? fact.normalized_numeric_value.toLocaleString() : "-"} ${fact.normalized_scale || ''} ${fact.normalized_currency || ''}`}>
                              {fact.normalized_numeric_value != null ? fact.normalized_numeric_value.toLocaleString() : "-"} {fact.normalized_scale} {fact.normalized_currency}
                            </p>
                          </div>
                        </div>

                        {/* Context Pills */}
                        <div className="flex flex-wrap gap-1.5 pt-2">
                          {fact.time_context && <span className="text-[10px] font-medium px-2 py-0.5 bg-blue-50 text-blue-700 border border-blue-100 rounded flex items-center gap-1"><Info size={10}/> {fact.time_context}</span>}
                          {fact.scope && <span className="text-[10px] font-medium px-2 py-0.5 bg-purple-50 text-purple-700 border border-purple-100 rounded">{fact.scope}</span>}
                          {fact.geography && <span className="text-[10px] font-medium px-2 py-0.5 bg-pink-50 text-pink-700 border border-pink-100 rounded">{fact.geography}</span>}
                          {fact.sign_convention_applied && <span className="text-[10px] font-medium px-2 py-0.5 bg-red-50 text-red-700 border border-red-100 rounded flex items-center gap-1"><ShieldAlert size={10}/> Sign Conv.</span>}
                        </div>
                      </div>

                      {/* Evidence Accordion (simplified) */}
                      {fact.evidence && (
                        <div className="mt-5 pt-4 border-t border-neutral-100">
                          <p className="text-[10px] font-bold text-neutral-400 uppercase tracking-widest mb-2">
                            Source Evidence
                          </p>
                          <p className="text-xs text-neutral-600 leading-relaxed bg-neutral-50 p-3 rounded-md border border-neutral-100 border-l-2 border-l-neutral-300" title={fact.evidence}>
                            &quot;{fact.evidence}&quot;
                          </p>
                        </div>
                      )}
                    </motion.div>
                  ))
                )}
              </motion.div>

            ) : (

              <motion.div 
                key="rels"
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="max-w-4xl mx-auto space-y-6 pb-20"
              >
                {relationships.length === 0 ? (
                  <div className="py-24 text-center text-neutral-400 bg-white rounded-2xl border border-neutral-200 border-dashed">
                    <GitMerge size={32} className="mx-auto mb-4 opacity-50 text-neutral-500" />
                    <p className="text-base font-medium text-neutral-700">No knowledge graph built yet</p>
                    <p className="text-sm mt-1 text-neutral-500">Click &quot;Compute Logic&quot; in the sidebar after uploading PDFs.</p>
                  </div>
                ) : (
                  relationships.map((rel: Relationship) => {
                    const isCorroborate = rel.relationship_type === 'CORROBORATES';
                    const isContradict = rel.relationship_type === 'CONTRADICTS';
                    const isReconciled = rel.relationship_type === 'EXPLAINABLE_CONTRADICTION';
                    
                    return (
                      <motion.div 
                        key={rel.id} 
                        layout
                        className="bg-white rounded-xl overflow-hidden shadow-[0_1px_2px_rgba(0,0,0,0.03)] border border-neutral-200 hover:shadow-md transition-shadow"
                      >
                        <div className="p-5">
                          <div className="flex items-center justify-between mb-4">
                            <div className={`flex items-center gap-1.5 font-bold px-2.5 py-1 rounded-md text-xs uppercase tracking-wider border ${
                              isCorroborate ? 'bg-emerald-50 border-emerald-200 text-emerald-800' :
                              isContradict ? 'bg-red-50 border-red-200 text-red-800' :
                              'bg-amber-50 border-amber-200 text-amber-800'
                            }`}>
                              {isCorroborate && <CheckCircle2 size={14} />}
                              {isContradict && <ShieldAlert size={14} />}
                              {isReconciled && <Info size={14} />}
                              {rel.relationship_type.replace("_", " ")}
                            </div>
                            <div className="flex items-center gap-2">
                              <span className="text-[11px] font-bold text-neutral-400 uppercase tracking-widest">Confidence</span>
                              <div className="w-16 h-1.5 bg-neutral-100 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full ${isCorroborate ? 'bg-emerald-500' : isContradict ? 'bg-red-500' : 'bg-amber-500'}`} 
                                  style={{ width: `${Math.round(rel.confidence * 100)}%` }} 
                                />
                              </div>
                              <span className="text-[11px] font-bold text-neutral-700">{Math.round(rel.confidence * 100)}%</span>
                            </div>
                          </div>
                          
                          <p className="text-neutral-700 text-sm leading-relaxed bg-neutral-50 px-4 py-3 rounded-lg border border-neutral-100 mb-4">
                            {rel.explanation}
                          </p>
                          
                          <div className="flex items-center justify-between text-xs text-neutral-500 bg-white border border-neutral-200 rounded-lg p-2.5 shadow-sm">
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-neutral-700">Fact A:</span>
                              <span className="font-mono bg-neutral-100 px-1.5 py-0.5 rounded text-neutral-600 border border-neutral-200/50">{rel.fact_a_id}</span>
                            </div>
                            <ChevronRight size={14} className="text-neutral-300" />
                            <div className="flex items-center gap-2">
                              <span className="font-semibold text-neutral-700">Fact B:</span>
                              <span className="font-mono bg-neutral-100 px-1.5 py-0.5 rounded text-neutral-600 border border-neutral-200/50">{rel.fact_b_id}</span>
                            </div>
                          </div>
                        </div>
                      </motion.div>
                    );
                  })
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </main>

      <style jsx global>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: transparent;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background-color: #cbd5e1;
          border-radius: 20px;
        }
      `}</style>
    </div>
  );
}
