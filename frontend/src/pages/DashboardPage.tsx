import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api, Classroom, ReportSummary } from '../api/client';
import { Navbar } from '../components/Navbar';
import { CreateClassroomModal } from '../components/CreateClassroomModal';
import { JoinClassroomModal } from '../components/JoinClassroomModal';
import {
  Plus,
  Link2,
  Users,
  FileCode2,
  FileText,
  ChevronRight,
} from 'lucide-react';

export const DashboardPage: React.FC = () => {
  const [classrooms, setClassrooms] = useState<Classroom[]>([]);
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [createOpen, setCreateOpen] = useState(false);
  const [joinOpen, setJoinOpen] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [cList, rList] = await Promise.all([
        api.getClassrooms(),
        api.getMyReports(),
      ]);
      setClassrooms(cList);
      setReports(rList);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return (
    <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
      <Navbar onCreateClick={() => setCreateOpen(true)} onJoinClick={() => setJoinOpen(true)} />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1 w-full">
        {/* Header Title */}
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between pb-8 mb-8 border-b border-olive-700/80 gap-4">
          <div>
            <h1 className="text-3xl sm:text-4xl font-display font-extrabold uppercase tracking-wide text-cream-200">
              Student Dashboard
            </h1>
            <p className="text-xs sm:text-sm text-olive-400 mt-1">
              Peer-to-peer code similarity with equal permissions and complete source privacy.
            </p>
          </div>

          <div className="flex items-center space-x-3 w-full sm:w-auto">
            <button
              onClick={() => setCreateOpen(true)}
              className="flex-1 sm:flex-none px-6 py-3 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 font-display font-bold text-xs uppercase tracking-wider shadow-lg shadow-cream-200/15 transition flex items-center justify-center space-x-2"
            >
              <Plus className="w-4 h-4 stroke-[2.5]" />
              <span>Create Classroom</span>
            </button>
            <button
              onClick={() => setJoinOpen(true)}
              className="flex-1 sm:flex-none px-6 py-3 rounded-full bg-olive-900 hover:bg-olive-850 text-cream-200 font-display font-semibold text-xs uppercase tracking-wider border border-olive-700 transition flex items-center justify-center space-x-2"
            >
              <Link2 className="w-4 h-4" />
              <span>Join with Link</span>
            </button>
          </div>
        </div>

        {/* My Classrooms */}
        <div className="mb-12">
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-display font-bold uppercase tracking-widest text-cream-200 flex items-center space-x-2">
              <Users className="w-4 h-4 text-cream-300" />
              <span>Enrolled Classrooms</span>
            </h2>
            <span className="text-xs text-olive-400 font-mono">{classrooms.length} active</span>
          </div>

          {loading ? (
            <div className="p-12 text-center text-olive-500 text-xs uppercase tracking-wider">Loading classrooms...</div>
          ) : classrooms.length === 0 ? (
            <div className="p-10 rounded-3xl bg-olive-900 border border-olive-700 text-center">
              <div className="w-12 h-12 rounded-2xl bg-cream-200/10 text-cream-200 mx-auto flex items-center justify-center mb-3">
                <Users className="w-6 h-6" />
              </div>
              <h3 className="text-base font-display font-bold text-cream-200 mb-1 uppercase">No Classrooms Yet</h3>
              <p className="text-xs text-olive-400 max-w-sm mx-auto mb-6">
                Create a new comparison session with a custom threshold (e.g. 2, 3, or 5 students) or join with a link.
              </p>
              <div className="flex justify-center gap-3">
                <button
                  onClick={() => setCreateOpen(true)}
                  className="px-5 py-2.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 font-display font-bold text-xs uppercase tracking-wider shadow-md"
                >
                  Create Classroom
                </button>
                <button
                  onClick={() => setJoinOpen(true)}
                  className="px-5 py-2.5 rounded-full bg-olive-850 hover:bg-olive-800 text-cream-200 font-display font-semibold text-xs uppercase tracking-wider border border-olive-700"
                >
                  Join Link
                </button>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {classrooms.map((c) => {
                const threshold = c.min_submissions || 5;
                const isComplete = c.status === 'COMPLETED';
                const isAnalyzing = c.status === 'ANALYZING';

                return (
                  <Link
                    key={c.id}
                    to={`/classrooms/${c.id}`}
                    className="group p-6 rounded-3xl bg-olive-900 border border-olive-700 hover:border-cream-300 shadow-xl transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <span
                          className={`px-3 py-1 rounded-full text-[10px] font-display font-bold tracking-wider uppercase ${
                            isComplete
                              ? 'bg-cream-200 text-olive-950 font-bold'
                              : isAnalyzing
                              ? 'bg-olive-700 text-cream-200'
                              : 'bg-olive-850 text-olive-300 border border-olive-700'
                          }`}
                        >
                          {c.status.replace(/_/g, ' ')}
                        </span>
                        {c.my_anonymous_label && (
                          <span className="text-[11px] font-mono px-2 py-0.5 rounded-lg bg-olive-950 border border-olive-700 text-cream-200">
                            {c.my_anonymous_label}
                          </span>
                        )}
                      </div>

                      <h3 className="text-base font-display font-bold uppercase tracking-wide text-cream-100 group-hover:text-cream-200 transition-colors line-clamp-1 mb-1">
                        {c.title}
                      </h3>
                      {c.description && (
                        <p className="text-xs text-olive-400 line-clamp-2 mb-4 leading-relaxed font-sans">
                          {c.description}
                        </p>
                      )}
                    </div>

                    <div className="mt-5 pt-4 border-t border-olive-700/60 flex items-center justify-between text-xs text-olive-400">
                      <div className="flex items-center space-x-3 font-mono">
                        <span className="flex items-center space-x-1">
                          <Users className="w-3.5 h-3.5 text-olive-500" />
                          <span>{c.participant_count}</span>
                        </span>
                        <span className="flex items-center space-x-1">
                          <FileCode2 className="w-3.5 h-3.5 text-olive-500" />
                          <span className={c.valid_submission_count >= threshold ? 'text-cream-200 font-bold' : ''}>
                            {c.valid_submission_count} / {threshold}
                          </span>
                        </span>
                      </div>

                      <span className="text-cream-200 group-hover:translate-x-1 transition-transform inline-flex items-center font-display uppercase tracking-wider font-bold text-[11px]">
                        Open <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                      </span>
                    </div>
                  </Link>
                );
              })}
            </div>
          )}
        </div>

        {/* Recent Private Reports */}
        <div>
          <div className="flex items-center justify-between mb-5">
            <h2 className="text-sm font-display font-bold uppercase tracking-widest text-cream-200 flex items-center space-x-2">
              <FileText className="w-4 h-4 text-cream-300" />
              <span>Recent Private Reports</span>
            </h2>
          </div>

          {reports.length === 0 ? (
            <div className="p-8 rounded-3xl bg-olive-900/50 border border-olive-700/60 text-center text-xs text-olive-400">
              No similarity reports available yet. Once a classroom reaches its threshold, your private report will appear here.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {reports.map((r) => (
                <Link
                  key={r.report_id}
                  to={`/reports/${r.report_id}`}
                  className="group p-6 rounded-3xl bg-olive-900 border border-olive-700 hover:border-cream-300 shadow-xl transition-all"
                >
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-[10px] font-mono text-olive-400 uppercase tracking-widest">
                      Report v{r.report_version}
                    </span>
                    <span className="text-xs font-mono font-bold text-cream-200 bg-olive-850 px-2.5 py-0.5 rounded-full border border-olive-700">
                      {r.highest_similarity}% max match
                    </span>
                  </div>

                  <h3 className="text-sm font-display font-bold uppercase tracking-wide text-cream-100 group-hover:text-cream-200 transition-colors line-clamp-1 mb-4">
                    {r.classroom_title}
                  </h3>

                  <div className="flex items-center justify-between text-xs text-olive-400 pt-3 border-t border-olive-700/60">
                    <span className="font-mono text-[11px]">{r.comparisons_count} peer comparisons</span>
                    <span className="text-cream-200 font-display uppercase tracking-wider font-bold text-[11px] flex items-center">
                      View Report <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </main>

      <CreateClassroomModal
        isOpen={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={() => fetchData()}
      />
      <JoinClassroomModal
        isOpen={joinOpen}
        onClose={() => setJoinOpen(false)}
        onJoined={() => fetchData()}
      />
    </div>
  );
};
