"use client";

import { useState, useEffect } from "react";

export default function Home() {
  const [documents, setDocuments] = useState([]);
  const [facts, setFacts] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const docRes = await fetch("http://localhost:8000/api/documents/");
      setDocuments(await docRes.json());
      const factRes = await fetch("http://localhost:8000/api/facts/");
      setFacts(await factRes.json());
      const relRes = await fetch("http://localhost:8000/api/relationships/");
      setRelationships(await relRes.json());
    } catch (e) {
      console.error(e);
    }
  };

  const uploadFile = async (e: any) => {
    const file = e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);
    setLoading(true);
    try {
      await fetch("http://localhost:8000/api/documents/upload", {
        method: "POST",
        body: formData,
      });
      fetchData();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const triggerExtraction = async (id: number) => {
    setLoading(true);
    try {
      await fetch(`http://localhost:8000/api/documents/${id}/extract`, { method: "POST" });
      fetchData();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const computeRelationships = async () => {
    setLoading(true);
    try {
      await fetch("http://localhost:8000/api/relationships/compute", { method: "POST" });
      fetchData();
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  return (
    <main className="p-8 font-sans bg-gray-50 min-h-screen text-black">
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-bold mb-8 text-blue-900">Fact Knowledge Layer</h1>
        {loading && <p className="text-blue-500 font-semibold mb-4 animate-pulse">Processing...</p>}
        
        <section className="mb-12">
          <h2 className="text-2xl font-semibold mb-4 border-b pb-2">1. Documents</h2>
          <input type="file" onChange={uploadFile} className="mb-4 block w-full p-2 border rounded" accept=".pdf" />
          <ul className="space-y-2">
            {documents.map((doc: any) => (
              <li key={doc.id} className="p-4 border rounded bg-white shadow-sm flex justify-between items-center">
                <span className="font-medium text-gray-800">{doc.filename} <span className="text-sm text-gray-500 ml-2">Status: {doc.status}</span></span>
                {doc.status === "PARSED" && (
                  <button className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded transition" onClick={() => triggerExtraction(doc.id)}>
                    Extract Facts
                  </button>
                )}
              </li>
            ))}
          </ul>
        </section>

        <section className="mb-12">
          <div className="flex justify-between items-center mb-4 border-b pb-2">
            <h2 className="text-2xl font-semibold">2. Relationships</h2>
            <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white font-medium rounded transition" onClick={computeRelationships}>
              Compute Cross-Document Relationships
            </button>
          </div>
          <div className="grid gap-4 md:grid-cols-2">
            {relationships.map((rel: any) => (
              <div key={rel.id} className="p-5 border rounded bg-white shadow-md">
                <div className="flex justify-between">
                  <span className={`font-bold text-lg ${rel.relationship_type === 'CONTRADICTS' ? 'text-red-600' : rel.relationship_type === 'CORROBORATES' ? 'text-green-600' : 'text-orange-500'}`}>
                    {rel.relationship_type}
                  </span>
                  <span className="text-sm text-gray-500 bg-gray-100 px-2 py-1 rounded">Conf: {Math.round(rel.confidence * 100)}%</span>
                </div>
                <p className="mt-3 text-gray-700 text-sm leading-relaxed">{rel.explanation}</p>
                <div className="mt-4 pt-3 border-t text-xs text-gray-500 flex justify-between">
                  <span>Fact A ID: <span className="font-mono bg-gray-100 px-1">{rel.fact_a_id}</span></span>
                  <span>Fact B ID: <span className="font-mono bg-gray-100 px-1">{rel.fact_b_id}</span></span>
                </div>
              </div>
            ))}
            {relationships.length === 0 && <p className="text-gray-500 italic">No relationships computed yet.</p>}
          </div>
        </section>

        <section>
          <h2 className="text-2xl font-semibold mb-4 border-b pb-2">3. Extracted Facts Directory</h2>
          <div className="grid gap-4 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {facts.map((fact: any) => (
              <div key={fact.id} className="p-5 border rounded bg-white shadow hover:shadow-md transition">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="font-bold text-lg text-gray-800 leading-tight">{fact.subject}</h3>
                  <span className="text-xs bg-blue-100 text-blue-800 font-mono px-2 py-1 rounded">ID: {fact.id}</span>
                </div>
                <div className="space-y-1 text-sm text-gray-600">
                  <p><span className="font-semibold text-gray-700">Predicate:</span> {fact.predicate}</p>
                  <p><span className="font-semibold text-gray-700">Value:</span> <span className="bg-green-50 text-green-800 px-1 font-medium">{fact.object_value} {fact.unit}</span></p>
                  {fact.time_context && <p><span className="font-semibold text-gray-700">Time Context:</span> {fact.time_context}</p>}
                  {(fact.scope || fact.geography) && <p><span className="font-semibold text-gray-700">Scope/Geog:</span> {fact.scope} {fact.geography ? `| ${fact.geography}` : ''}</p>}
                </div>
                {fact.evidence && fact.evidence.length > 0 && (
                  <div className="mt-3 text-xs bg-yellow-50 border border-yellow-100 p-2 rounded text-yellow-800">
                    <span className="font-semibold block mb-1">Evidence:</span>
                    <span className="italic">"{fact.evidence[0]}"</span>
                  </div>
                )}
              </div>
            ))}
            {facts.length === 0 && <p className="text-gray-500 italic col-span-full">No facts extracted yet. Upload a document and extract facts.</p>}
          </div>
        </section>
      </div>
    </main>
  );
}
