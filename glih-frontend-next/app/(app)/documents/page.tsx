"use client";
import { useState, useRef } from "react";
import Header from "@/components/Header";
import { ragQuery, BASE, authHeaders } from "@/lib/api";
import { usePermissions } from "@/hooks/usePermissions";

const COLLECTIONS = ["lineage-sops", "glih-default"];

const INITIAL_DOCS = [
  { id: "sop-001", name: "SOP-COLD-CHAIN-003", type: "SOP",  collection: "lineage-sops", size: "2.4 KB", added: "2025-01-15", chunks: 3  },
  { id: "sop-002", name: "SOP-ROUTE-007",       type: "SOP",  collection: "lineage-sops", size: "89 KB",  added: "2025-01-15", chunks: 12 },
  { id: "sop-003", name: "SOP-IOT-002",          type: "SOP",  collection: "lineage-sops", size: "67 KB",  added: "2025-01-15", chunks: 9  },
  { id: "doc-001", name: "Lineage-SOPs Full",    type: "Data", collection: "lineage-sops", size: "2.4 KB", added: "2025-03-24", chunks: 3  },
];

export default function DocumentsPage() {
  const { can } = usePermissions();
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<any>(null);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"query" | "manage">("query");

  // Manage tab state
  const [docs, setDocs] = useState(INITIAL_DOCS);
  const [showModal, setShowModal] = useState(false);
  const [ingestMode, setIngestMode] = useState<"file" | "text" | "url">("url");
  const [collection, setCollection] = useState("lineage-sops");
  const [pastedText, setPastedText] = useState("");
  const [docName, setDocName] = useState("");
  const [urlInput, setUrlInput] = useState("");
  const [ingesting, setIngesting] = useState(false);
  const [ingestResult, setIngestResult] = useState<{ chunks: number; collection: string } | null>(null);
  const [ingestError, setIngestError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function search() {
    if (!query.trim()) return;
    setSearching(true);
    setResults(null);
    setError(null);
    try {
      const data = await ragQuery(query, "lineage-sops", 4);
      setResults(data);
    } catch (e: any) {
      setError(e.message || "Query failed");
    } finally {
      setSearching(false);
    }
  }

  async function handleIngest() {
    setIngesting(true);
    setIngestError(null);
    setIngestResult(null);
    try {
      let data: any;
      const today = new Date().toISOString().slice(0, 10);

      if (ingestMode === "url") {
        if (!urlInput.trim()) throw new Error("No URL entered");
        const urls = urlInput.split("\n").map(u => u.trim()).filter(Boolean);
        // Use AbortController with 5 minute timeout for slow government PDFs
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 300000); // 5 min
        const res = await fetch(`${BASE}/ingest/url`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ urls, collection, chunk_size: 800 }),
          signal: controller.signal,
        });
        clearTimeout(timeoutId);
        data = await res.json();
        if (!res.ok) throw new Error(data.detail || res.statusText);
        if ((data.ingested ?? 0) === 0) throw new Error(data.detail || "0 chunks extracted — URLs may be inaccessible or image-only");
        const successUrls = urls.filter((u: string) => !(data.errors ?? []).some((e: string) => e.startsWith(u)));
        successUrls.forEach((u: string) => {
          const name = decodeURIComponent(u.split("/").pop()?.replace(/\.[^.]+$/, "") || "URL Import");
          setDocs(prev => [...prev, { id: `doc-${Date.now()}-${name}`, name, type: "Data", collection, size: "—", added: today, chunks: data.ingested }]);
        });
        setIngestResult({ chunks: data.ingested ?? 0, collection: data.collection ?? collection });
        if (data.errors?.length) {
          setIngestError(`⚠ ${data.errors.length} URL(s) failed (timeout/blocked): ${data.errors.map((e: string) => e.split(":")[0].split("/").pop()).join(", ")}`);
        }
        setUrlInput("");
      } else if (ingestMode === "file") {
        const files = fileRef.current?.files;
        if (!files || files.length === 0) throw new Error("No file selected");
        const fd = new FormData();
        Array.from(files).forEach(f => fd.append("files", f));
        const token = localStorage.getItem("glih_access_token");
        const res = await fetch(`${BASE}/ingest/file?collection=${encodeURIComponent(collection)}`, {
          method: "POST",
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          body: fd,
        });
        data = await res.json();
        if (!res.ok) throw new Error(data.detail || res.statusText);
        if ((data.ingested ?? 0) === 0) throw new Error("0 chunks extracted — try a .txt file or use URL ingest for PDFs");
        Array.from(files).forEach(f => {
          setDocs(prev => [...prev, {
            id: `doc-${Date.now()}-${f.name}`, name: f.name.replace(/\.[^.]+$/, ""),
            type: "Data", collection, size: `${(f.size / 1024).toFixed(1)} KB`, added: today, chunks: data.ingested ?? 0,
          }]);
        });
      } else {
        if (!pastedText.trim()) throw new Error("No text entered");
        const res = await fetch(`${BASE}/ingest`, {
          method: "POST",
          headers: authHeaders(),
          body: JSON.stringify({ texts: [pastedText], collection, metadatas: [{ source: docName || "manual-paste", type: "manual" }] }),
        });
        data = await res.json();
        if (!res.ok) throw new Error(data.detail || res.statusText);
        setDocs(prev => [...prev, {
          id: `doc-${Date.now()}`, name: docName || "Manual Paste",
          type: "Data", collection, size: `${(new Blob([pastedText]).size / 1024).toFixed(1)} KB`, added: today, chunks: data.ingested ?? 0,
        }]);
      }

      if (ingestMode !== "url") {
        setIngestResult({ chunks: data.ingested ?? 0, collection: data.collection ?? collection });
      }
      setPastedText("");
      setDocName("");
      if (fileRef.current) fileRef.current.value = "";
    } catch (e: any) {
      setIngestError(e.message);
    } finally {
      setIngesting(false);
    }
  }

  function closeModal() {
    setShowModal(false);
    setIngestResult(null);
    setIngestError(null);
    setUrlInput("");
    setPastedText("");
    setDocName("");
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      <Header title="Documents" subtitle="RAG knowledge base · lineage-sops · powered by GPT-4o" />
      <div style={{ flex: 1, overflow: "auto", padding: 20 }}>

        {/* Tabs */}
        <div style={{ display: "flex", gap: 0, marginBottom: 16, borderBottom: "1px solid var(--border)" }}>
          {[["query", "🔍 RAG Query"], ["manage", "📁 Manage Documents"]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id as "query" | "manage")} style={{
              padding: "8px 18px", background: "transparent", border: "none",
              borderBottom: tab === id ? "2px solid var(--teal)" : "2px solid transparent",
              color: tab === id ? "var(--teal)" : "var(--text-muted)",
              fontSize: "0.8rem", fontWeight: tab === id ? 700 : 400, cursor: "pointer", marginBottom: -1,
            }}>{label}</button>
          ))}
        </div>

        {tab === "query" && (
          <div>
            <div className="card" style={{ padding: 16, marginBottom: 16 }}>
              <div style={{ fontSize: "0.65rem", color: "var(--teal)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 10 }}>
                ● LIVE — GPT-4o + ChromaDB
              </div>
              <div style={{ display: "flex", gap: 10 }}>
                <input
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === "Enter" && search()}
                  placeholder="Ask about cold chain SOPs — e.g. What do I do if seafood exceeds 4°C?"
                  style={{
                    flex: 1, background: "var(--bg-secondary)", border: "1px solid var(--border)",
                    borderRadius: 6, padding: "10px 14px", color: "var(--text-primary)", fontSize: "0.8rem",
                  }}
                />
                <button className="btn-primary" onClick={search} disabled={searching}>
                  {searching ? "Querying..." : "Ask"}
                </button>
              </div>
              <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
                {[
                  "What do I do if seafood exceeds 4°C for 30 minutes?",
                  "Dairy breach protocol steps",
                  "Frozen foods temperature threshold",
                  "Who to notify during a temperature breach?",
                ].map(q => (
                  <button key={q} className="btn-ghost" style={{ fontSize: "0.65rem" }}
                    onClick={() => setQuery(q)}>
                    {q}
                  </button>
                ))}
              </div>
            </div>

            {searching && (
              <div className="card" style={{ padding: 24, textAlign: "center" }}>
                <div style={{ color: "var(--teal)", fontSize: "0.85rem", marginBottom: 6 }}>⚡ Querying RAG pipeline...</div>
                <div style={{ color: "var(--text-muted)", fontSize: "0.7rem" }}>Embedding → Vector search → GPT-4o synthesis</div>
              </div>
            )}

            {error && (
              <div style={{ background: "#1a0505", border: "1px solid #7f1d1d", borderRadius: 8, padding: 16, color: "#f87171", fontSize: "0.75rem" }}>
                ✗ Error: {error} — make sure backend is running on port 9001
              </div>
            )}

            {results && (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div className="card" style={{ padding: 16, borderColor: "var(--teal-dim)" }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 10 }}>
                    <span style={{ fontSize: "0.65rem", fontWeight: 700, color: "var(--teal)", letterSpacing: "0.08em" }}>⚡ GPT-4o ANSWER</span>
                    <span style={{ fontSize: "0.6rem", color: "var(--text-muted)" }}>
                      {results.retrieved} chunks retrieved · {results.collection}
                    </span>
                  </div>
                  <div style={{ fontSize: "0.78rem", color: "var(--text-primary)", lineHeight: 1.7, whiteSpace: "pre-wrap" }}>
                    {results.answer}
                  </div>
                </div>

                {results.citations?.length > 0 && (
                  <div>
                    <div style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", marginBottom: 8 }}>SOURCE CITATIONS</div>
                    {results.citations.map((c: any, i: number) => (
                      <div key={i} className="card" style={{ padding: 12, marginBottom: 8 }}>
                        <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 6 }}>
                          <span style={{ color: "var(--amber)", fontSize: "0.7rem", fontWeight: 700 }}>📄 {c.source}</span>
                          <span style={{ fontSize: "0.62rem", color: "var(--text-muted)" }}>chunk {c.chunk_id} · dist {c.distance?.toFixed(3)}</span>
                        </div>
                        <div style={{ fontSize: "0.7rem", color: "var(--text-secondary)", fontStyle: "italic", lineHeight: 1.5 }}>"{c.snippet}"</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {tab === "manage" && (
          <div>
            <div style={{ display: "flex", justifyContent: "flex-end", marginBottom: 14 }}>
              {can("documents:ingest") && (
                <button className="btn-primary" onClick={() => setShowModal(true)}>+ Ingest Document</button>
              )}
            </div>
            <div className="card" style={{ overflow: "hidden" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.75rem" }}>
                <thead>
                  <tr style={{ background: "var(--bg-secondary)", borderBottom: "1px solid var(--border)" }}>
                    {["Name", "Type", "Collection", "Size", "Chunks", "Added"].map(h => (
                      <th key={h} style={{ textAlign: "left", padding: "10px 14px", color: "var(--text-muted)", fontSize: "0.6rem", fontWeight: 600, letterSpacing: "0.06em" }}>{h.toUpperCase()}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {docs.map(d => (
                    <tr key={d.id} style={{ borderBottom: "1px solid var(--border)", cursor: "pointer" }}
                      onMouseEnter={e => (e.currentTarget as HTMLElement).style.background = "var(--bg-card)"}
                      onMouseLeave={e => (e.currentTarget as HTMLElement).style.background = "transparent"}
                    >
                      <td style={{ padding: "10px 14px", color: "var(--teal)", fontWeight: 600 }}>{d.name}</td>
                      <td style={{ padding: "10px 14px" }}><span className="badge badge-transit">{d.type}</span></td>
                      <td style={{ padding: "10px 14px", color: "var(--text-muted)", fontFamily: "monospace", fontSize: "0.68rem" }}>{d.collection}</td>
                      <td style={{ padding: "10px 14px", color: "var(--text-secondary)" }}>{d.size}</td>
                      <td style={{ padding: "10px 14px", color: "var(--text-secondary)" }}>{d.chunks}</td>
                      <td style={{ padding: "10px 14px", color: "var(--text-muted)" }}>{d.added}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Ingest Modal */}
      {showModal && (
        <div style={{
          position: "fixed", inset: 0, background: "rgba(0,0,0,0.7)", display: "flex",
          alignItems: "center", justifyContent: "center", zIndex: 1000,
        }} onClick={e => { if (e.target === e.currentTarget) closeModal(); }}>
          <div className="card" style={{ width: 520, padding: 24, position: "relative" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
              <div style={{ fontSize: "0.9rem", fontWeight: 700, color: "var(--text-primary)" }}>Ingest Document</div>
              <button onClick={closeModal} style={{ background: "none", border: "none", color: "var(--text-muted)", fontSize: "1.2rem", cursor: "pointer", lineHeight: 1 }}>×</button>
            </div>

            {/* Mode toggle */}
            <div style={{ display: "flex", gap: 0, marginBottom: 18, background: "var(--bg-secondary)", borderRadius: 6, padding: 3 }}>
              {([["url", "🔗 From URL"], ["file", "📄 Upload File"], ["text", "✏️ Paste Text"]] as const).map(([m, label]) => (
                <button key={m} onClick={() => setIngestMode(m)} style={{
                  flex: 1, padding: "6px 0", border: "none", borderRadius: 4, cursor: "pointer", fontSize: "0.72rem", fontWeight: 600,
                  background: ingestMode === m ? "var(--bg-card)" : "transparent",
                  color: ingestMode === m ? "var(--teal)" : "var(--text-muted)",
                }}>
                  {label}
                </button>
              ))}
            </div>

            {/* Collection selector */}
            <div style={{ marginBottom: 14 }}>
              <label style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", display: "block", marginBottom: 6 }}>COLLECTION</label>
              <select value={collection} onChange={e => setCollection(e.target.value)} style={{
                width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)",
                borderRadius: 6, padding: "8px 12px", color: "var(--text-primary)", fontSize: "0.8rem",
              }}>
                {COLLECTIONS.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            {ingestMode === "url" ? (
              <div style={{ marginBottom: 14 }}>
                <label style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", display: "block", marginBottom: 6 }}>
                  DOCUMENT URL(S) <span style={{ fontWeight: 400 }}>— one per line</span>
                </label>
                <textarea value={urlInput} onChange={e => setUrlInput(e.target.value)}
                  placeholder={"https://www.gcca.org/...guide.pdf\nhttps://www.fsis.usda.gov/...guidelines.pdf"}
                  style={{
                    width: "100%", height: 100, background: "var(--bg-secondary)", border: "1px solid var(--border)",
                    borderRadius: 6, padding: "10px 12px", color: "var(--text-primary)", fontSize: "0.72rem",
                    fontFamily: "monospace", resize: "vertical",
                  }}
                />
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", marginTop: 4 }}>
                  Backend fetches &amp; parses the URL — works with PDF, HTML, and plain text pages
                </div>
                <div style={{ marginTop: 10, display: "flex", flexDirection: "column", gap: 4 }}>
                  <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.06em" }}>QUICK-ADD</div>
                  {[
                    ["GCCA Best Practices 2024", "https://www.gcca.org/wp-content/uploads/2016/07/2024-Final-Draft-GCCA-Cold-Chain-Best-Practices-Guide-Global.pdf"],
                    ["USDA FSIS Warehouse Guide", "https://www.fsis.usda.gov/sites/default/files/media_file/2020-07/Guidance_Document_Warehouses.pdf"],
                    ["USDA Transport Safety", "https://www.ams.usda.gov/sites/default/files/media/FSIS%20Safety%20and%20Security%20Guidelines%20for%20the%20Transportation%20and%20Distribution%20of%20Meat,%20Poultry,%20and%20Egg%20Products.pdf"],
                  ].map(([label, url]) => (
                    <button key={url} className="btn-ghost" style={{ textAlign: "left", fontSize: "0.65rem", padding: "4px 8px" }}
                      onClick={() => setUrlInput(prev => prev ? prev + "\n" + url : url)}>
                      + {label}
                    </button>
                  ))}
                </div>
              </div>
            ) : ingestMode === "file" ? (
              <div style={{ marginBottom: 14 }}>
                <label style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", display: "block", marginBottom: 6 }}>FILE(S)</label>
                <input ref={fileRef} type="file" multiple accept=".txt,.pdf,.md,.csv,.json" style={{
                  width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)",
                  borderRadius: 6, padding: "8px 12px", color: "var(--text-primary)", fontSize: "0.75rem", cursor: "pointer",
                }} />
                <div style={{ fontSize: "0.62rem", color: "var(--text-muted)", marginTop: 4 }}>Supported: .txt · .pdf · .md · .csv · .json — use URL mode for PDFs if 0 chunks returned</div>
              </div>
            ) : (
              <>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", display: "block", marginBottom: 6 }}>DOCUMENT NAME</label>
                  <input value={docName} onChange={e => setDocName(e.target.value)} placeholder="e.g. SOP-HAZMAT-009"
                    style={{
                      width: "100%", background: "var(--bg-secondary)", border: "1px solid var(--border)",
                      borderRadius: 6, padding: "8px 12px", color: "var(--text-primary)", fontSize: "0.8rem",
                    }}
                  />
                </div>
                <div style={{ marginBottom: 14 }}>
                  <label style={{ fontSize: "0.65rem", color: "var(--text-muted)", fontWeight: 700, letterSpacing: "0.08em", display: "block", marginBottom: 6 }}>TEXT CONTENT</label>
                  <textarea value={pastedText} onChange={e => setPastedText(e.target.value)}
                    placeholder="Paste your document text here..."
                    style={{
                      width: "100%", height: 160, background: "var(--bg-secondary)", border: "1px solid var(--border)",
                      borderRadius: 6, padding: "10px 12px", color: "var(--text-primary)", fontSize: "0.75rem",
                      fontFamily: "monospace", resize: "vertical",
                    }}
                  />
                </div>
              </>
            )}

            {ingestError && (
              <div style={{ background: "#1a0505", border: "1px solid #7f1d1d", borderRadius: 6, padding: 10, color: "#f87171", fontSize: "0.72rem", marginBottom: 12 }}>
                ✗ {ingestError}
              </div>
            )}

            {ingestResult && (
              <div style={{ background: "#052e16", border: "1px solid #14532d", borderRadius: 6, padding: 10, color: "#4ade80", fontSize: "0.72rem", marginBottom: 12 }}>
                ✓ Ingested {ingestResult.chunks} chunk{ingestResult.chunks !== 1 ? "s" : ""} into <span style={{ fontFamily: "monospace" }}>{ingestResult.collection}</span>
              </div>
            )}

            <div style={{ display: "flex", gap: 10, justifyContent: "flex-end" }}>
              <button className="btn-ghost" onClick={closeModal}>Cancel</button>
              <button className="btn-primary" onClick={handleIngest} disabled={ingesting} style={{ minWidth: 120 }}>
                {ingesting ? "Ingesting..." : "⚡ Ingest"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
