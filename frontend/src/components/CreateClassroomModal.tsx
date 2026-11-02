import React, { useState } from 'react';
import { api, Classroom } from '../api/client';
import { X, Sparkles, AlertCircle, Users, Check } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (classroom: Classroom) => void;
}

export const CreateClassroomModal: React.FC<Props> = ({ isOpen, onClose, onCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [minSubmissions, setMinSubmissions] = useState<number>(5);
  const [deadline, setDeadline] = useState('');
  const [maxParticipants, setMaxParticipants] = useState<number | undefined>(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!isOpen) return null;

  const quickOptions = [
    { value: 2, label: '2', desc: 'Pairs / Partner' },
    { value: 3, label: '3', desc: 'Study Group' },
    { value: 5, label: '5', desc: 'Standard' },
    { value: 10, label: '10', desc: 'Class Section' },
  ];

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Please provide a classroom title');
      return;
    }
    if (minSubmissions < 2) {
      setError('Minimum submissions threshold must be at least 2');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const payload: any = {
        title: title.trim(),
        description: description.trim() || undefined,
        language: 'cpp',
        min_submissions: Number(minSubmissions),
      };
      if (deadline) {
        payload.deadline = new Date(deadline).toISOString();
      }
      if (maxParticipants && maxParticipants > 0) {
        payload.max_participants = Number(maxParticipants);
      }

      const classroom = await api.createClassroom(payload);
      onCreated(classroom);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create classroom');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-3xl bg-olive-900 border border-olive-700 shadow-2xl overflow-hidden p-6 sm:p-7 text-cream-100">
        <div className="flex items-center justify-between pb-4 border-b border-olive-700/80">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-cream-200 text-olive-950 flex items-center justify-center font-bold shadow-md">
              <Sparkles className="w-4 h-4 text-olive-950" />
            </div>
            <div>
              <h3 className="text-lg font-display uppercase tracking-wider font-bold text-cream-200">
                Create Session
              </h3>
              <p className="text-[11px] text-olive-400">Equal peer code comparison</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-olive-400 hover:text-cream-200 hover:bg-olive-800 transition"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="mt-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
              Classroom / Assignment Title *
            </label>
            <input
              type="text"
              required
              placeholder="e.g. CS201 — Binary Search Trees"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition"
            />
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
              Description (Optional)
            </label>
            <textarea
              rows={2}
              placeholder="Assignment prompt or instructions for your classmates"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-4 py-2 rounded-xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition resize-none"
            />
          </div>

          {/* EASILY CONFIGURABLE SUBMISSION THRESHOLD (User Requested Feature) */}
          <div className="p-4 rounded-2xl bg-olive-850 border border-olive-700/80 space-y-2.5">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-cream-200 uppercase tracking-wider flex items-center space-x-1.5">
                <Users className="w-3.5 h-3.5 text-cream-300" />
                <span>Submissions Needed to Start Analysis</span>
              </label>
              <span className="text-xs font-mono font-bold text-olive-950 bg-cream-200 px-2 py-0.5 rounded-full">
                {minSubmissions} students
              </span>
            </div>

            <p className="text-[11px] text-olive-400 leading-tight">
              Analysis automatically begins once this number of distinct participants submit valid code.
            </p>

            {/* Quick selector buttons */}
            <div className="grid grid-cols-4 gap-2 pt-1">
              {quickOptions.map((opt) => (
                <button
                  type="button"
                  key={opt.value}
                  onClick={() => setMinSubmissions(opt.value)}
                  className={`py-2 px-1.5 rounded-xl text-center border transition-all ${
                    minSubmissions === opt.value
                      ? 'bg-cream-200 text-olive-950 font-bold border-cream-200 shadow-md'
                      : 'bg-olive-800 text-olive-300 border-olive-700 hover:border-olive-600 hover:text-cream-200'
                  }`}
                >
                  <div className="text-sm leading-none">{opt.label}</div>
                  <div className="text-[9px] mt-0.5 opacity-80">{opt.desc}</div>
                </button>
              ))}
            </div>

            {/* Or custom input */}
            <div className="flex items-center space-x-2 pt-1 text-xs">
              <span className="text-olive-400 text-[11px]">Or custom count:</span>
              <input
                type="number"
                min={2}
                max={500}
                value={minSubmissions}
                onChange={(e) => setMinSubmissions(Math.max(2, parseInt(e.target.value) || 2))}
                className="w-20 px-2.5 py-1 rounded-lg bg-olive-800 border border-olive-700 text-cream-100 text-xs font-mono focus:outline-none focus:border-cream-200 text-center"
              />
              <span className="text-olive-400 text-[11px]">students</span>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div>
              <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                Deadline (Optional)
              </label>
              <input
                type="datetime-local"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-olive-850 border border-olive-700 text-cream-100 text-xs focus:outline-none focus:border-cream-200 transition"
              />
            </div>
            <div>
              <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                Max Capacity (Optional)
              </label>
              <input
                type="number"
                min={2}
                max={500}
                placeholder="Unlimited"
                value={maxParticipants || ''}
                onChange={(e) => setMaxParticipants(e.target.value ? parseInt(e.target.value) : undefined)}
                className="w-full px-3 py-2 rounded-xl bg-olive-850 border border-olive-700 text-cream-100 text-xs focus:outline-none focus:border-cream-200 transition"
              />
            </div>
          </div>

          <div className="p-3 rounded-xl bg-olive-950/60 border border-olive-700/50 text-[11px] text-olive-400 leading-relaxed">
            <strong className="text-cream-200">Equal Rights Guarantee:</strong> As creator, you join as standard participant <span className="text-cream-200 font-mono font-bold">Peer A</span>. No one can view raw classmate code.
          </div>

          <div className="flex items-center justify-end space-x-3 pt-3 border-t border-olive-700/60">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full text-olive-400 hover:text-cream-200 text-xs font-semibold transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-bold uppercase tracking-wider shadow-lg shadow-cream-200/10 transition disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Session'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
