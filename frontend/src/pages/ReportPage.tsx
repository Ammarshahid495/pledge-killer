import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, ReportDetail, MatchDetail, MatchRegion } from '../api/client';
import { Navbar } from '../components/Navbar';
import { CodeViewer } from '../components/CodeViewer';
import {
  ShieldCheck,
  EyeOff,
  Scale,
  Cpu,
  ArrowLeft,
  Download,
  AlertCircle,
  ChevronRight,
  Info,
} from 'lucide-react';

export const ReportPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<MatchDetail | null>(null);
  const [selectedRegion, setSelectedRegion] = useState<MatchRegion | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!reportId) return;
    setLoading(true);
    api
      .getReportDetail(reportId)
      .then((data) => {
        setReport(data);
        if (data.matches && data.matches.length > 0) {
          const firstMatch = data.matches[0];
          setSelectedMatch(firstMatch);
          if (firstMatch.regions && firstMatch.regions.length > 0) {
            setSelectedRegion(firstMatch.regions[0]);
          }
        }
      })
      .catch((err) => {
        setError(err.message || 'Failed to load report');
      })
      .finally(() => setLoading(false));
  }, [reportId]);

  const handleDownloadJSON = async () => {
    if (!reportId) return;
    try {
      await api.downloadReportJSON(reportId);
    } catch (err: any) {
      window.alert(err.message || 'Failed to download report');
    }
  };

  const handleDownloadPDF = () => {
    if (!report) return;

    const printWindow = window.open('', '_blank');
    if (!printWindow) return;

    const now = new Date().toLocaleDateString('en-US', {
      year: 'numeric', month: 'long', day: 'numeric',
    });

    const escHtml = (str: string) =>
      String(str ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');

    /* ---- Build function rows ---- */
    const fnRows = report.matches
      .flatMap((m) =>
        (m.matched_functions || []).map(
          (fn) => `
          <tr>
            <td>${escHtml(fn.function_name)}()</td>
            <td>${escHtml(m.peer_label)}: ${escHtml(fn.peer_function_name)}()</td>
            <td>${fn.similarity_percentage}%</td>
            <td class="${fn.match_type === 'LOGICAL' ? 'logical' : 'verbatim'}">${fn.match_type === 'LOGICAL' ? 'Logical Clone' : 'Verbatim Copy'}</td>
            <td>${escHtml(fn.verdict)}</td>
          </tr>`
        )
      )
      .join('');

    /* ---- Build regions rows ---- */
    const regionRows = report.matches
      .flatMap((m) =>
        (m.regions || []).map(
          (r, i) => `
          <tr>
            <td>${escHtml(m.peer_label)}</td>
            <td>L${r.my_start_line}–${r.my_end_line}</td>
            <td>${r.peer_start_line ? `L${r.peer_start_line}–${r.peer_end_line}` : '—'}</td>
            <td class="${r.match_type === 'LOGICAL' ? 'logical' : 'verbatim'}">${r.match_type === 'LOGICAL' ? 'Logical' : 'Verbatim'}</td>
            <td>${r.function_name ? escHtml(r.function_name) : '—'}</td>
            <td>—</td>
          </tr>`
        )
      )
      .join('');

    /* ---- Build highlighted source lines ---- */
    const allRegions = report.matches.flatMap((m) => m.regions || []);
    const highlightedLineMap: Record<number, string> = {};
    allRegions.forEach((r) => {
      for (let ln = r.my_start_line; ln <= r.my_end_line; ln++) {
        highlightedLineMap[ln] = r.match_type === 'LOGICAL' ? '#fef2f2' : '#f0fdf4';
      }
    });
    const sourceLines = (report.my_source_code || '').split('\n');
    const codeHtml = sourceLines
      .map((line, i) => {
        const ln = i + 1;
        const bg = highlightedLineMap[ln];
        const style = bg ? `style="background:${bg}"` : '';
        return `<tr ${style}><td class="ln">${ln}</td><td class="code-line">${escHtml(line) || ' '}</td></tr>`;
      })
      .join('');

    /* ---- Peer summary rows ---- */
    const peerRows = report.matches
      .map(
        (m) => `
        <tr>
          <td>${escHtml(m.peer_label)}</td>
          <td>${m.similarity_score}%</td>
          <td>${m.regions.length} blocks</td>
          <td>${m.matched_token_count} tokens</td>
          <td>${m.directional_coverage_to_peer}%</td>
        </tr>`
      )
      .join('');

    const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <title>Pledge Fighter — Similarity Report</title>
  <style>
    *{box-sizing:border-box;margin:0;padding:0}
    body{font-family:'Segoe UI',Arial,sans-serif;font-size:10pt;color:#1C201A;background:#fff;padding:14mm}
    h1{font-size:22pt;font-weight:900;text-transform:uppercase;letter-spacing:.04em;color:#1C201A;margin-bottom:2px}
    h2{font-size:12pt;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#3F473B;margin:18px 0 6px}
    .subtitle{font-size:9pt;color:#697763;margin-bottom:14px}
    .header-row{display:flex;align-items:center;justify-content:space-between;padding-bottom:10px;border-bottom:2px solid #2C3229;margin-bottom:14px}
    .badge{background:#F2E9D6;color:#1C201A;font-weight:700;font-size:8pt;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:.06em}
    .stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}
    .stat-card{background:#F7F2E7;border:1px solid #E7DCBE;border-radius:10px;padding:10px 12px}
    .stat-value{font-size:18pt;font-weight:900;color:#1C201A}
    .stat-label{font-size:7pt;text-transform:uppercase;letter-spacing:.08em;color:#697763;margin-top:2px}
    table{width:100%;border-collapse:collapse;margin-bottom:14px;font-size:8.5pt}
    th{background:#2C3229;color:#F7F2E7;text-align:left;padding:6px 8px;font-size:7.5pt;text-transform:uppercase;letter-spacing:.05em}
    td{border-bottom:1px solid #E7DCBE;padding:5px 8px;vertical-align:top}
    tr:nth-child(even) td{background:#FCF9F3}
    .logical{color:#b91c1c;font-weight:700}
    .verbatim{color:#047857;font-weight:700}
    .code-table{width:100%;border-collapse:collapse;font-size:7.5pt;font-family:'Courier New',monospace}
    .code-table .ln{width:36px;text-align:right;color:#9C8C61;padding:1px 6px 1px 0;user-select:none;border-right:1px solid #E7DCBE}
    .code-table .code-line{padding:1px 6px;white-space:pre-wrap;word-break:break-all}
    .legend{display:flex;gap:16px;font-size:8pt;margin-bottom:8px}
    .legend span{display:flex;align-items:center;gap:5px}
    .dot{width:10px;height:10px;border-radius:50%;display:inline-block}
    .dot-logical{background:#ef4444}
    .dot-verbatim{background:#22c55e}
    .disclaimer{margin-top:16px;padding:10px 12px;background:#F7F2E7;border:1px solid #E7DCBE;border-radius:8px;font-size:8pt;color:#525D4D;line-height:1.5}
    .page-break{page-break-before:always}
    @page{size:A4 portrait;margin:12mm}
    @media print{body{padding:0}}
  </style>
</head>
<body>

<div class="header-row">
  <div>
    <h1>⚔ PLEDGE FIGHTER</h1>
    <p class="subtitle">Peer-to-Peer Code Similarity Report — Strictly Private &amp; Confidential</p>
  </div>
  <div>
    <span class="badge">Generated: ${now}</span>
  </div>
</div>

<p style="font-size:9pt;color:#525D4D;margin-bottom:12px">
  <strong>Classroom:</strong> ${escHtml(report.classroom_title)} &nbsp;|&nbsp;
  <strong>Engine:</strong> Winnowing v${escHtml(String(report.engine_version))} &nbsp;|&nbsp;
  <strong>Report ID:</strong> <span style="font-family:monospace">${escHtml(String(reportId))}</span>
</p>

<h2>Summary</h2>
<div class="stat-grid">
  <div class="stat-card"><div class="stat-value">${report.highest_similarity}%</div><div class="stat-label">Highest Similarity</div></div>
  <div class="stat-card"><div class="stat-value">${report.comparisons_count}</div><div class="stat-label">Peer Comparisons</div></div>
  <div class="stat-card"><div class="stat-value">${report.total_matching_regions}</div><div class="stat-label">Matching Regions</div></div>
  <div class="stat-card"><div class="stat-value">${report.matches.reduce((a, m) => a + (m.matched_functions?.length || 0), 0)}</div><div class="stat-label">Functions Compared</div></div>
</div>

<h2>Peer-Level Similarity</h2>
<table>
  <tr><th>Peer</th><th>Similarity</th><th>Blocks</th><th>Tokens Matched</th><th>Coverage →</th></tr>
  ${peerRows || '<tr><td colspan="5" style="color:#9C8C61">No peer comparisons available.</td></tr>'}
</table>

<h2>Function-Level Analysis</h2>
<table>
  <tr><th>Your Function</th><th>Peer Function</th><th>Similarity</th><th>Type</th><th>Verdict</th></tr>
  ${fnRows || '<tr><td colspan="5" style="color:#9C8C61">No function-level matches extracted.</td></tr>'}
</table>

<h2>Matched Code Regions</h2>
<table>
  <tr><th>Peer</th><th>Your Lines</th><th>Peer Lines</th><th>Type</th><th>Function</th><th>Tokens</th></tr>
  ${regionRows || '<tr><td colspan="6" style="color:#9C8C61">No matched regions.</td></tr>'}
</table>

<div class="page-break"></div>

<h2>Annotated Source Code</h2>
<div class="legend">
  <span><span class="dot dot-verbatim"></span> Verbatim (exact copy)</span>
  <span><span class="dot dot-logical"></span> Logical Clone (same logic, renamed vars)</span>
</div>
<table class="code-table">
  ${codeHtml}
</table>

<div class="disclaimer">
  <strong>Honest Reporting Notice:</strong> Similarity scores indicate structural and token-sequence overlap — NOT proof of academic misconduct. Common algorithms, data structures, and starter templates naturally share token patterns. This report is for self-awareness only. Always consult your academic integrity policy before drawing conclusions.
</div>

</body>
</html>`;

    printWindow.document.write(html);
    printWindow.document.close();
    printWindow.focus();
    setTimeout(() => printWindow.print(), 600);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-xs uppercase tracking-widest text-olive-400">
          Loading your private similarity report...
        </div>
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
        <Navbar />
        <div className="max-w-md mx-auto my-20 p-8 rounded-3xl bg-olive-900 border border-olive-700 text-center">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
          <h2 className="text-lg font-display font-bold uppercase text-cream-200 mb-2">Report Unavailable</h2>
          <p className="text-xs text-olive-400 mb-6">{error || 'Could not find report'}</p>
          <Link to="/dashboard" className="px-5 py-2.5 rounded-full bg-cream-200 text-olive-950 text-xs font-bold uppercase tracking-wider">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const activeRegions = selectedMatch ? selectedMatch.regions : report.all_regions;

  return (
    <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
      <Navbar />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full space-y-8">
        {/* Breadcrumb & Action */}
        <div className="flex items-center justify-between pb-4 border-b border-olive-700/80">
          <Link
            to={`/classrooms/${report.classroom_id}`}
            className="text-xs font-bold font-display uppercase tracking-wider text-olive-400 hover:text-cream-200 flex items-center space-x-1.5 transition"
          >
            <ArrowLeft className="w-4 h-4 stroke-[2.5]" />
            <span>Back to {report.classroom_title}</span>
          </Link>

          <div className="flex items-center space-x-2">
            <button
              onClick={handleDownloadPDF}
              className="px-4 py-2 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 border border-cream-300 text-xs font-display font-bold uppercase tracking-wider flex items-center space-x-1.5 transition shadow-md shadow-cream-200/10"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download PDF</span>
            </button>
            <button
              onClick={handleDownloadJSON}
              className="px-4 py-2 rounded-full bg-olive-900 hover:bg-olive-850 text-cream-200 border border-olive-700 text-xs font-display font-bold uppercase tracking-wider flex items-center space-x-1.5 transition"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Raw JSON</span>
            </button>
          </div>
        </div>

        {/* Top Summary Banner */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl">
            <span className="text-[10px] font-display font-bold uppercase tracking-widest text-olive-400 block mb-1">
              Highest Similarity
            </span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-4xl font-black font-display text-cream-200">{report.highest_similarity}%</span>
              <span className="text-xs font-mono text-olive-400">max match</span>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl">
            <span className="text-[10px] font-display font-bold uppercase tracking-widest text-olive-400 block mb-1">
              Peer Comparisons
            </span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-4xl font-black font-display text-cream-200">{report.comparisons_count}</span>
              <span className="text-xs font-mono text-olive-400">classmates</span>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl">
            <span className="text-[10px] font-display font-bold uppercase tracking-widest text-olive-400 block mb-1">
              Matching Regions
            </span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-4xl font-black font-display text-cream-200">{report.total_matching_regions}</span>
              <span className="text-xs font-mono text-olive-400">code spans</span>
            </div>
          </div>

          <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl">
            <span className="text-[10px] font-display font-bold uppercase tracking-widest text-olive-400 block mb-1">
              Analysis Engine
            </span>
            <div className="flex items-baseline space-x-1.5">
              <span className="text-2xl font-bold font-display text-cream-200">Winnowing</span>
              <span className="text-xs font-mono text-olive-400">v{report.engine_version}</span>
            </div>
          </div>
        </div>

        {/* Main Comparison Area: Anonymous Peer List + Code Viewer */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Comparisons with Anonymous Peers */}
          <div className="space-y-4">
            <h3 className="text-xs font-display font-bold text-cream-200 uppercase tracking-widest flex items-center justify-between">
              <span>Peer Matches</span>
              <span className="text-[11px] text-olive-400 font-normal">Click to view region highlights</span>
            </h3>

            {report.matches.length === 0 ? (
              <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 text-center text-xs text-olive-400">
                No significant similarity detected with any classroom peers.
              </div>
            ) : (
              <div className="space-y-3">
                {report.matches.map((m) => {
                  const isSelected = selectedMatch?.match_id === m.match_id;

                  return (
                    <div
                      key={m.match_id}
                      className={`p-5 rounded-2xl border transition-all ${
                        isSelected
                          ? 'bg-olive-850 border-cream-200 shadow-xl shadow-cream-200/5'
                          : 'bg-olive-900 border-olive-700 hover:border-olive-600 hover:bg-olive-850/50'
                      }`}
                    >
                      <div
                        onClick={() => {
                          setSelectedMatch(m);
                          if (m.regions && m.regions.length > 0) {
                            setSelectedRegion(m.regions[0]);
                          }
                        }}
                        className="cursor-pointer"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-mono text-xs font-bold text-cream-100 flex items-center space-x-2">
                            <span className="w-2.5 h-2.5 rounded-full bg-cream-200 inline-block" />
                            <span>{m.peer_label}</span>
                          </span>
                          <span className="text-xs font-mono font-black px-2.5 py-0.5 rounded-full bg-cream-200 text-olive-950">
                            {m.similarity_score}%
                          </span>
                        </div>

                        <div className="flex items-center justify-between text-[11px] text-olive-400 font-mono">
                          <span>{m.regions.length} matching {m.regions.length === 1 ? 'block' : 'blocks'}</span>
                          <span>{m.matched_token_count} tokens</span>
                        </div>

                        <div className="mt-2 text-[10px] text-olive-400 font-mono">
                          Coverage: You → {m.peer_label}: {m.directional_coverage_to_peer}%
                        </div>
                      </div>

                      {/* Matching Blocks Breakdown */}
                      {isSelected && m.regions && m.regions.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-olive-700/80 space-y-1.5">
                          <span className="text-[10px] font-display uppercase tracking-widest text-olive-400 block mb-1">
                            Matching Line Blocks (Click to jump):
                          </span>
                          <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                            {m.regions.map((reg, idx) => {
                              const isRegionActive =
                                selectedRegion?.my_start_line === reg.my_start_line &&
                                selectedRegion?.my_end_line === reg.my_end_line;
                              const isLogical = reg.match_type === 'LOGICAL';

                              return (
                                <button
                                  key={idx}
                                  onClick={() => setSelectedRegion(reg)}
                                  className={`w-full text-left p-2.5 rounded-xl text-[11px] font-mono transition flex flex-col gap-1 border ${
                                    isRegionActive
                                      ? isLogical
                                        ? 'bg-rose-500/20 text-rose-200 border-rose-500 font-bold'
                                        : 'bg-emerald-500/20 text-emerald-200 border-emerald-500 font-bold'
                                      : 'bg-olive-900/80 hover:bg-olive-800 text-cream-200/90 border-olive-700/60'
                                  }`}
                                >
                                  <div className="flex items-center justify-between">
                                    <span className="flex items-center space-x-1.5">
                                      <span
                                        className={`w-2 h-2 rounded-full ${
                                          isLogical ? 'bg-rose-500' : 'bg-emerald-500'
                                        }`}
                                      />
                                      <span>
                                        Block #{idx + 1}: Lines {reg.my_start_line}–{reg.my_end_line}
                                      </span>
                                    </span>
                                    <span
                                      className={`text-[9px] font-bold uppercase tracking-wider px-1.5 py-0.5 rounded ${
                                        isLogical
                                          ? 'bg-rose-500/20 text-rose-300'
                                          : 'bg-emerald-500/20 text-emerald-300'
                                      }`}
                                    >
                                      {isLogical ? 'LOGICAL' : 'VERBATIM'}
                                    </span>
                                  </div>

                                  <div className="text-[10px] text-olive-400 flex items-center justify-between">
                                    {reg.peer_start_line && (
                                      <span>
                                        ↔ {m.peer_label} L{reg.peer_start_line}–{reg.peer_end_line}
                                      </span>
                                    )}
                                    {reg.function_name && (
                                      <span className="text-cream-300/70">[{reg.function_name}]</span>
                                    )}
                                  </div>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      )}

                      {/* Function-Level Similarity Breakdown */}
                      {isSelected && m.matched_functions && m.matched_functions.length > 0 && (
                        <div className="mt-4 pt-3 border-t border-olive-700/80 space-y-2">
                          <span className="text-[10px] font-display uppercase tracking-widest text-cream-200 font-bold block">
                            Function-Level Similarity Report:
                          </span>
                          <div className="space-y-1.5 max-h-56 overflow-y-auto pr-1">
                            {m.matched_functions.map((fn, fIdx) => {
                              const isLogical = fn.match_type === 'LOGICAL';

                              return (
                                <div
                                  key={fIdx}
                                  onClick={() => {
                                    // Jump to function start line
                                    const matchingReg = m.regions.find(
                                      (r) => r.my_start_line <= fn.my_end_line && r.my_end_line >= fn.my_start_line
                                    );
                                    if (matchingReg) {
                                      setSelectedRegion(matchingReg);
                                    }
                                  }}
                                  className={`p-2.5 rounded-xl border text-[11px] font-mono cursor-pointer transition ${
                                    isLogical
                                      ? 'bg-rose-500/10 border-rose-500/30 hover:bg-rose-500/20'
                                      : 'bg-emerald-500/10 border-emerald-500/30 hover:bg-emerald-500/20'
                                  }`}
                                >
                                  <div className="flex items-center justify-between mb-1">
                                    <span className="font-bold text-cream-100 flex items-center space-x-1.5">
                                      <span
                                        className={`w-2 h-2 rounded-full ${
                                          isLogical ? 'bg-rose-500' : 'bg-emerald-500'
                                        }`}
                                      />
                                      <span>{fn.function_name}()</span>
                                      {fn.peer_function_name !== fn.function_name && (
                                        <span className="text-olive-400 font-normal">
                                          ↔ {fn.peer_function_name}()
                                        </span>
                                      )}
                                    </span>
                                    <span
                                      className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                        isLogical
                                          ? 'bg-rose-500/20 text-rose-300'
                                          : 'bg-emerald-500/20 text-emerald-300'
                                      }`}
                                    >
                                      {fn.similarity_percentage}% {isLogical ? 'Logical Clone' : 'Verbatim'}
                                    </span>
                                  </div>
                                  <p className="text-[10px] text-olive-300 leading-tight">
                                    {fn.verdict}
                                  </p>
                                  <div className="text-[10px] text-olive-400 mt-1 flex justify-between">
                                    <span>Lines {fn.my_start_line}–{fn.my_end_line}</span>
                                    <span>{fn.matched_tokens} tokens</span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            {/* Honest Similarity Statement */}
            <div className="p-5 rounded-3xl bg-olive-900 border border-olive-700 text-xs text-olive-400 space-y-2">
              <div className="flex items-center space-x-2 text-cream-200 font-display font-bold uppercase tracking-wider text-xs">
                <Info className="w-4 h-4 text-cream-300" />
                <span>Honest Reporting Policy</span>
              </div>
              <p className="text-[11px] leading-relaxed font-sans">
                Similarity indicates structural and token sequence overlap, not proof of misconduct. Common libraries, data structures, and starter templates naturally share token patterns.
              </p>
            </div>
          </div>

          {/* Right Column: Highlighted Code Viewer */}
          <div className="lg:col-span-2">
            <CodeViewer
              sourceCode={report.my_source_code}
              regions={activeRegions}
              activePeerLabel={selectedMatch?.peer_label}
              activeMatchScore={selectedMatch?.similarity_score}
              selectedRegion={selectedRegion}
              onSelectRegion={setSelectedRegion}
            />
          </div>
        </div>
      </main>
    </div>
  );
};
