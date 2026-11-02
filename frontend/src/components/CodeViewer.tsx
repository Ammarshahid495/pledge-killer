import React, { useMemo, useRef, useEffect, useState } from 'react';
import { MatchRegion } from '../api/client';
import { ShieldCheck, EyeOff, Layers, ChevronDown, ChevronUp, Sparkles, Code2, AlertTriangle, CheckCircle } from 'lucide-react';

interface CodeViewerProps {
  sourceCode: string;
  regions: MatchRegion[];
  activePeerLabel?: string;
  activeMatchScore?: number;
  selectedRegion?: MatchRegion | null;
  onSelectRegion?: (region: MatchRegion) => void;
}

export const CodeViewer: React.FC<CodeViewerProps> = ({
  sourceCode,
  regions,
  activePeerLabel,
  activeMatchScore,
  selectedRegion,
  onSelectRegion,
}) => {
  const lines = useMemo(() => sourceCode.split('\n'), [sourceCode]);
  const [activeRegionIndex, setActiveRegionIndex] = useState<number>(0);
  const lineRefs = useRef<{ [key: number]: HTMLTableRowElement | null }>({});

  // Map each line number to matching regions
  const lineHighlightMap = useMemo(() => {
    const map = new Map<number, { region: MatchRegion; index: number; isStart: boolean; isEnd: boolean }[]>();
    regions.forEach((r, idx) => {
      for (let l = r.my_start_line; l <= r.my_end_line; l++) {
        const arr = map.get(l) || [];
        arr.push({
          region: r,
          index: idx,
          isStart: l === r.my_start_line,
          isEnd: l === r.my_end_line,
        });
        map.set(l, arr);
      }
    });
    return map;
  }, [regions]);

  // Auto-scroll when selected region changes
  useEffect(() => {
    if (selectedRegion && selectedRegion.my_start_line) {
      const el = lineRefs.current[selectedRegion.my_start_line];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  }, [selectedRegion]);

  const scrollToRegion = (idx: number) => {
    if (idx >= 0 && idx < regions.length) {
      setActiveRegionIndex(idx);
      const reg = regions[idx];
      if (onSelectRegion) {
        onSelectRegion(reg);
      }
      const el = lineRefs.current[reg.my_start_line];
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }
  };

  const totalMatchedLines = useMemo(() => {
    const matchedLineSet = new Set<number>();
    regions.forEach((r) => {
      for (let l = r.my_start_line; l <= r.my_end_line; l++) {
        matchedLineSet.add(l);
      }
    });
    return matchedLineSet.size;
  }, [regions]);

  return (
    <div className="rounded-3xl bg-olive-900 border border-olive-700 overflow-hidden shadow-2xl flex flex-col h-full text-cream-100">
      {/* Top Header */}
      <div className="px-6 py-4 bg-olive-950 border-b border-olive-700/80 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <div className="flex space-x-1.5">
            <div className="w-2.5 h-2.5 rounded-full bg-rose-400" />
            <div className="w-2.5 h-2.5 rounded-full bg-cream-300" />
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          </div>
          <span className="text-xs font-mono font-medium text-cream-200">
            solution.cpp (Your Submission)
          </span>
          <span className="text-[11px] font-mono text-olive-400 px-2.5 py-0.5 rounded-full bg-olive-900 border border-olive-700">
            {lines.length} lines
          </span>
        </div>

        <div className="flex items-center space-x-3 text-xs">
          {activePeerLabel && (
            <div className="flex items-center space-x-1.5 bg-cream-200/10 px-3 py-1 rounded-full border border-cream-200/20 text-cream-200 font-mono text-xs">
              <Sparkles className="w-3.5 h-3.5 text-cream-200 shrink-0" />
              <span>
                Matching <strong>{activePeerLabel}</strong> ({activeMatchScore}%)
              </span>
            </div>
          )}

          <div className="flex items-center space-x-1 px-3 py-1 rounded-full bg-olive-900 border border-olive-700 text-olive-300 text-[11px] font-mono">
            <ShieldCheck className="w-3.5 h-3.5 text-cream-300 shrink-0" />
            <span>Private & Encrypted</span>
          </div>
        </div>
      </div>

      {/* Highlighting Legend & Navigation Bar */}
      <div className="px-6 py-2.5 bg-olive-900/90 border-b border-olive-700/80 flex flex-wrap items-center justify-between gap-3 text-xs">
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-rose-500 inline-block shadow-sm shadow-rose-500/50" />
            <span className="text-[11px] font-mono font-bold text-rose-300">
              Red: Logical Similarity (same logic / renamed variables)
            </span>
          </div>
          <div className="flex items-center space-x-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block shadow-sm shadow-emerald-500/50" />
            <span className="text-[11px] font-mono font-bold text-emerald-300">
              Green: Verbatim Match (exact direct copy)
            </span>
          </div>
        </div>

        {regions.length > 0 && (
          <div className="flex items-center space-x-2">
            <span className="text-[11px] text-olive-400 font-mono">
              Block {activeRegionIndex + 1} of {regions.length} ({totalMatchedLines} lines matched)
            </span>
            <button
              onClick={() => scrollToRegion(Math.max(0, activeRegionIndex - 1))}
              disabled={activeRegionIndex === 0}
              className="p-1 rounded-lg bg-olive-850 hover:bg-olive-800 disabled:opacity-30 text-cream-200 transition"
              title="Previous Match Block"
            >
              <ChevronUp className="w-4 h-4" />
            </button>
            <button
              onClick={() => scrollToRegion(Math.min(regions.length - 1, activeRegionIndex + 1))}
              disabled={activeRegionIndex === regions.length - 1}
              className="p-1 rounded-lg bg-olive-850 hover:bg-olive-800 disabled:opacity-30 text-cream-200 transition"
              title="Next Match Block"
            >
              <ChevronDown className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Code Table Area */}
      <div className="p-2 bg-olive-950/70 overflow-auto font-mono text-xs leading-relaxed max-h-[640px] select-text">
        <table className="w-full border-collapse">
          <tbody>
            {lines.map((lineText, idx) => {
              const lineNum = idx + 1;
              const matches = lineHighlightMap.get(lineNum);
              const isHighlighted = matches && matches.length > 0;
              const startRegionMatch = matches?.find((m) => m.isStart);
              const isLogical = matches?.some((m) => m.region.match_type === 'LOGICAL');
              const isSelectedBlock =
                selectedRegion &&
                lineNum >= selectedRegion.my_start_line &&
                lineNum <= selectedRegion.my_end_line;

              return (
                <React.Fragment key={lineNum}>
                  {/* Banner header above the first line of a matching block */}
                  {startRegionMatch && (
                    <tr
                      className={
                        startRegionMatch.region.match_type === 'LOGICAL'
                          ? 'bg-rose-500/20 border-y border-rose-500/30'
                          : 'bg-emerald-500/20 border-y border-emerald-500/30'
                      }
                    >
                      <td colSpan={2} className="py-1 px-4 text-[11px] font-mono">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <span className="flex items-center space-x-2 font-bold">
                            <span
                              className={`w-2.5 h-2.5 rounded-full animate-pulse ${
                                startRegionMatch.region.match_type === 'LOGICAL'
                                  ? 'bg-rose-500'
                                  : 'bg-emerald-500'
                              }`}
                            />
                            <span
                              className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                                startRegionMatch.region.match_type === 'LOGICAL'
                                  ? 'bg-rose-500/20 text-rose-300 border-rose-500/30'
                                  : 'bg-emerald-500/20 text-emerald-300 border-emerald-500/30'
                              }`}
                            >
                              {startRegionMatch.region.match_type === 'LOGICAL'
                                ? 'Logical Similarity (Same Logic)'
                                : 'Verbatim Match (Exact Copy)'}
                            </span>
                            <span className="text-cream-200">
                              Block #{startRegionMatch.index + 1}: Lines {startRegionMatch.region.my_start_line}–
                              {startRegionMatch.region.my_end_line}
                            </span>
                            {startRegionMatch.region.peer_start_line && (
                              <span className="text-olive-300 font-normal">
                                ↔ aligns with {activePeerLabel || 'Peer'}&apos;s lines{' '}
                                <strong className="text-cream-200">
                                  {startRegionMatch.region.peer_start_line}–{startRegionMatch.region.peer_end_line}
                                </strong>
                              </span>
                            )}
                            {startRegionMatch.region.function_name && (
                              <span className="text-cream-300/80 font-mono text-[10px]">
                                [Function: {startRegionMatch.region.function_name}]
                              </span>
                            )}
                          </span>
                          <span className="text-[10px] text-olive-400 font-mono">
                            {startRegionMatch.region.matched_token_count} tokens
                          </span>
                        </div>
                      </td>
                    </tr>
                  )}

                  <tr
                    ref={(el) => {
                      lineRefs.current[lineNum] = el;
                    }}
                    className={`group transition-colors ${
                      isSelectedBlock
                        ? isLogical
                          ? 'bg-rose-500/25 border-l-4 border-rose-500'
                          : 'bg-emerald-500/25 border-l-4 border-emerald-500'
                        : isHighlighted
                        ? isLogical
                          ? 'bg-rose-500/10 hover:bg-rose-500/15 border-l-2 border-rose-500/70'
                          : 'bg-emerald-500/10 hover:bg-emerald-500/15 border-l-2 border-emerald-500/70'
                        : 'hover:bg-olive-850/50'
                    }`}
                  >
                    {/* Line number gutter */}
                    <td
                      className={`w-14 text-right pr-4 py-0.5 select-none font-mono text-[11px] align-top ${
                        isHighlighted
                          ? isLogical
                            ? 'text-rose-400 font-bold bg-rose-500/5'
                            : 'text-emerald-400 font-bold bg-emerald-500/5'
                          : 'text-olive-500 group-hover:text-olive-400'
                      }`}
                    >
                      {lineNum}
                    </td>

                    {/* Code content */}
                    <td className="py-0.5 px-3 text-cream-100 whitespace-pre font-mono text-xs">
                      <span
                        className={
                          isSelectedBlock
                            ? 'text-cream-100 font-medium'
                            : isHighlighted
                            ? isLogical
                              ? 'text-rose-200'
                              : 'text-emerald-200'
                            : 'text-cream-200/80'
                        }
                      >
                        {lineText || ' '}
                      </span>
                    </td>
                  </tr>
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer Info */}
      <div className="px-5 py-3 bg-olive-950 border-t border-olive-700/80 text-[11px] text-olive-400 flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-2">
          <Code2 className="w-3.5 h-3.5 text-cream-200" />
          <span>
            Highlighted in <strong className="text-rose-400">RED</strong> for logical / structural clones (renamed identifiers) and <strong className="text-emerald-400">GREEN</strong> for exact verbatim copies.
          </span>
        </div>
        <div className="flex items-center space-x-1.5 text-olive-400">
          <EyeOff className="w-3.5 h-3.5 text-cream-300" />
          <span>Peers never see your raw code; comparison is performed securely.</span>
        </div>
      </div>
    </div>
  );
};
