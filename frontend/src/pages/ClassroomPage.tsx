import React, { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import { api, Classroom, Submission } from '../api/client';
import { Navbar } from '../components/Navbar';
import { ThresholdProgressBar } from '../components/ThresholdProgressBar';
import {
  Copy,
  Check,
  UploadCloud,
  FileCode2,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  ArrowRight,
  FileText,
  Users,
  Trash2,
} from 'lucide-react';

export const ClassroomPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [classroom, setClassroom] = useState<Classroom | null>(null);
  const [submission, setSubmission] = useState<Submission | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const loadData = async () => {
    if (!id) return;
    try {
      const c = await api.getClassroom(id);
      setClassroom(c);

      try {
        const sub = await api.getMySubmission(id);
        setSubmission(sub);
      } catch {
        setSubmission(null);
      }
    } catch (err: any) {
      // If user landed on classroom page but is not a member yet, automatically join as equal peer
      if (err.message && (err.message.toLowerCase().includes('not a member') || err.message.toLowerCase().includes('forbidden'))) {
        try {
          const joined = await api.joinClassroom(id);
          setClassroom(joined);
          try {
            const sub = await api.getMySubmission(id);
            setSubmission(sub);
          } catch {
            setSubmission(null);
          }
          return;
        } catch (joinErr: any) {
          setError(joinErr.message || 'Failed to join classroom');
          return;
        }
      }
      setError(err.message || 'Failed to load classroom');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [id]);

  const getFullJoinUrl = () => {
    if (!classroom) return '';
    const token = classroom.join_token || (classroom.join_url ? classroom.join_url.split('/join/').pop() : '') || classroom.id;
    return `${window.location.origin}/join/${token}`;
  };

  const fallbackCopy = (text: string) => {
    try {
      const el = document.createElement('textarea');
      el.value = text;
      el.setAttribute('readonly', '');
      el.style.position = 'absolute';
      el.style.left = '-9999px';
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Ignored
    }
  };

  const handleCopyLink = () => {
    const fullUrl = getFullJoinUrl();
    if (!fullUrl) return;

    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(fullUrl)
        .then(() => {
          setCopied(true);
          setTimeout(() => setCopied(false), 2500);
        })
        .catch(() => {
          fallbackCopy(fullUrl);
        });
    } else {
      fallbackCopy(fullUrl);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!id) return;
    if (!file.name.toLowerCase().endsWith('.cpp')) {
      setError('Only .cpp source files are accepted');
      return;
    }
    if (file.size > 1048576) {
      setError('File exceeds 1 MB size limit');
      return;
    }

    setUploading(true);
    setError(null);
    try {
      const res = await api.uploadSubmission(id, file);
      setSubmission(res);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteSubmission = async () => {
    if (!id) return;
    if (!window.confirm('Are you sure you want to remove your submission? Your file will be withdrawn from similarity comparison.')) {
      return;
    }
    setDeleting(true);
    setError(null);
    try {
      await api.deleteMySubmission(id);
      setSubmission(null);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to remove submission');
    } finally {
      setDeleting(false);
    }
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
        <Navbar />
        <div className="flex-1 flex items-center justify-center text-xs uppercase tracking-widest text-olive-400">
          Loading classroom...
        </div>
      </div>
    );
  }

  if (!classroom) {
    return (
      <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
        <Navbar />
        <div className="max-w-md mx-auto my-20 p-8 rounded-3xl bg-olive-900 border border-olive-700 text-center">
          <AlertCircle className="w-10 h-10 text-rose-400 mx-auto mb-3" />
          <h2 className="text-lg font-display font-bold uppercase text-cream-200 mb-2">Classroom Not Found</h2>
          <p className="text-xs text-olive-400 mb-6">{error || 'You might not have joined this classroom yet.'}</p>
          <Link to="/dashboard" className="px-5 py-2.5 rounded-full bg-cream-200 text-olive-950 text-xs font-bold uppercase tracking-wider">
            Return to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  const threshold = classroom.min_submissions || 5;

  return (
    <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
      <Navbar />

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1 w-full space-y-8">
        {/* Header & Meta */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-olive-700/80">
          <div>
            <div className="flex items-center space-x-2.5 mb-2">
              <span className="px-3 py-1 rounded-full text-[10px] font-display font-bold tracking-wider bg-cream-200/10 text-cream-200 border border-cream-200/20 uppercase">
                C++ Session
              </span>
              {classroom.my_anonymous_label && (
                <span className="text-xs font-mono font-bold text-olive-300 px-3 py-1 rounded-full bg-olive-900 border border-olive-700">
                  You are: <strong className="text-cream-200">{classroom.my_anonymous_label}</strong>
                </span>
              )}
            </div>
            <h1 className="text-3xl sm:text-4xl font-display font-extrabold uppercase text-cream-200 tracking-wide">
              {classroom.title}
            </h1>
            {classroom.description && (
              <p className="text-xs sm:text-sm text-olive-400 mt-1 max-w-2xl leading-relaxed">
                {classroom.description}
              </p>
            )}
          </div>

          {/* Report Button if Ready */}
          {classroom.has_report && classroom.my_report_id && (
            <Link
              to={`/reports/${classroom.my_report_id}`}
              className="px-6 py-3.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 font-display font-bold text-xs uppercase tracking-wider shadow-xl shadow-cream-200/15 flex items-center space-x-2 transition self-start md:self-auto"
            >
              <FileText className="w-4 h-4 stroke-[2.5]" />
              <span>View Private Report</span>
              <ArrowRight className="w-4 h-4 stroke-[2.5]" />
            </Link>
          )}
        </div>

        {/* Shareable Invitation Link Banner */}
        <div className="p-5 sm:p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl space-y-3">
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
            <div className="space-y-0.5">
              <h3 className="text-xs font-display font-bold text-cream-200 uppercase tracking-widest flex items-center space-x-1.5">
                <span>Shareable Invitation Link</span>
              </h3>
              <p className="text-xs text-olive-400">
                Share with classmates. Everyone joins as equals; minimum threshold is <strong className="text-cream-200">{threshold} students</strong>.
              </p>
            </div>
            {copied && (
              <span className="text-xs font-bold text-cream-200 flex items-center space-x-1 bg-cream-200/10 px-3 py-1 rounded-full border border-cream-200/20">
                <Check className="w-3.5 h-3.5 text-cream-200 stroke-[2.5]" />
                <span>Copied to Clipboard!</span>
              </span>
            )}
          </div>

          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5 pt-1">
            <input
              type="text"
              readOnly
              value={getFullJoinUrl()}
              onClick={(e) => (e.target as HTMLInputElement).select()}
              placeholder="Generating joining link..."
              className="flex-1 px-4 py-2.5 rounded-2xl bg-olive-950 border border-olive-700 text-cream-200 font-mono text-xs select-all focus:outline-none focus:border-cream-300"
            />
            <button
              onClick={handleCopyLink}
              className="px-6 py-2.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-display font-bold uppercase tracking-wider flex items-center justify-center space-x-2 transition shadow-md shadow-cream-200/10 shrink-0"
            >
              {copied ? (
                <>
                  <Check className="w-4 h-4 text-olive-950 stroke-[2.5]" />
                  <span>Copied!</span>
                </>
              ) : (
                <>
                  <Copy className="w-4 h-4 text-olive-950" />
                  <span>Copy Link</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Configurable Submission Threshold Progress Bar */}
        <ThresholdProgressBar
          currentCount={classroom.valid_submission_count}
          threshold={threshold}
          status={classroom.status}
        />

        {error && (
          <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Assignment Upload Section */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <div className="p-6 sm:p-7 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-display font-bold uppercase tracking-wider text-cream-200 flex items-center space-x-2">
                  <UploadCloud className="w-5 h-5 text-cream-300" />
                  <span>{submission ? 'Replace Assignment (.cpp)' : 'Upload Your Assignment (.cpp)'}</span>
                </h3>
                <span className="text-[11px] font-mono text-olive-400">Max size: 1 MB</span>
              </div>

              {/* Drag and Drop Zone */}
              <div
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                className={`p-8 sm:p-10 rounded-2xl border-2 border-dashed transition-all cursor-pointer text-center ${
                  dragActive
                    ? 'border-cream-200 bg-cream-200/10'
                    : 'border-olive-700 hover:border-cream-300 bg-olive-950/60'
                }`}
              >
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".cpp"
                  className="hidden"
                  onChange={(e) => {
                    if (e.target.files && e.target.files[0]) {
                      handleFileUpload(e.target.files[0]);
                    }
                  }}
                />

                <div className="w-12 h-12 rounded-2xl bg-cream-200/10 text-cream-200 mx-auto flex items-center justify-center mb-3">
                  <FileCode2 className="w-6 h-6 text-cream-200" />
                </div>

                <p className="text-sm font-bold font-display uppercase tracking-wider text-cream-200 mb-1">
                  {uploading ? 'Validating and uploading...' : 'Drop your .cpp file here or click to browse'}
                </p>
                <p className="text-xs text-olive-400">
                  Only C++ source code is accepted. Executables, archives, and binaries are strictly rejected.
                </p>
              </div>

              {submission && (
                <div className="mt-5 p-4 rounded-2xl bg-olive-950 border border-olive-700 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-9 h-9 rounded-xl bg-cream-200 text-olive-950 flex items-center justify-center font-bold shrink-0">
                      <CheckCircle2 className="w-5 h-5" />
                    </div>
                    <div>
                      <p className="text-xs font-mono font-bold text-cream-200">
                        {submission.current_version?.original_filename || 'solution.cpp'}
                      </p>
                      <p className="text-[11px] font-mono text-olive-400">
                        Version {submission.current_version?.version_number} • {(submission.current_version?.file_size || 0)} bytes
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2.5 self-end sm:self-auto">
                    <span className="text-[10px] font-mono font-semibold text-olive-950 bg-cream-200 px-3 py-1 rounded-full uppercase tracking-wider">
                      Active Submission
                    </span>
                    <button
                      onClick={handleDeleteSubmission}
                      disabled={deleting}
                      className="px-3 py-1 rounded-full bg-rose-500/15 hover:bg-rose-500/25 text-rose-300 border border-rose-500/30 text-[11px] font-display font-bold uppercase tracking-wider transition flex items-center space-x-1.5 disabled:opacity-50"
                      title="Remove your uploaded file from this session"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                      <span>{deleting ? 'Removing...' : 'Remove File'}</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Source Code Preview */}
            {submission?.raw_code && (
              <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl">
                <h4 className="text-xs font-display font-bold uppercase tracking-wider text-cream-200 mb-3 flex items-center space-x-2">
                  <ShieldCheck className="w-4 h-4 text-cream-200" />
                  <span>Your Submitted Code Preview</span>
                </h4>
                <div className="p-4 rounded-2xl bg-olive-950 overflow-x-auto font-mono text-xs text-cream-100 max-h-72 border border-olive-700/80">
                  <pre>{submission.raw_code}</pre>
                </div>
              </div>
            )}
          </div>

          {/* Right Column: Privacy & Rules */}
          <div className="space-y-6">
            <div className="p-6 sm:p-7 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl space-y-4">
              <h3 className="text-xs font-display font-bold uppercase tracking-widest text-cream-200">
                Privacy Guarantees
              </h3>

              <div className="space-y-3.5 text-xs text-olive-400 leading-relaxed font-sans">
                <div className="flex items-start space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-cream-200 shrink-0 mt-0.5" />
                  <span>Other students cannot view or download your raw source code.</span>
                </div>
                <div className="flex items-start space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-cream-200 shrink-0 mt-0.5" />
                  <span>Other students cannot access your private similarity report.</span>
                </div>
                <div className="flex items-start space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-cream-200 shrink-0 mt-0.5" />
                  <span>Comparisons identify structural patterns using anonymous labels (<code className="text-cream-200 font-mono">Peer A</code>, <code className="text-cream-200 font-mono">Peer B</code>).</span>
                </div>
                <div className="flex items-start space-x-2.5">
                  <CheckCircle2 className="w-4 h-4 text-cream-200 shrink-0 mt-0.5" />
                  <span>Uploaded code is never compiled or executed.</span>
                </div>
              </div>
            </div>

            <div className="p-6 rounded-3xl bg-olive-900 border border-olive-700 shadow-xl space-y-3">
              <h3 className="text-xs font-display font-bold uppercase tracking-widest text-cream-200">
                Automated Threshold
              </h3>
              <p className="text-xs text-olive-400 leading-relaxed">
                When at least <strong className="text-cream-200">{threshold} distinct students</strong> upload valid assignments, similarity analysis begins automatically.
              </p>
              <p className="text-xs text-olive-400 leading-relaxed">
                Incremental analysis updates reports automatically as additional classmates submit.
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};
