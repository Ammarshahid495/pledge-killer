import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { X, Link2, AlertCircle } from 'lucide-react';

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onJoined?: () => void;
}

export const JoinClassroomModal: React.FC<Props> = ({ isOpen, onClose, onJoined }) => {
  const [tokenInput, setTokenInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const raw = tokenInput.trim();
    if (!raw) return;

    let token = raw;
    if (token.includes('/join/')) {
      const parts = token.split('/join/');
      token = parts[parts.length - 1] || token;
    } else if (token.includes('/classrooms/')) {
      const parts = token.split('/classrooms/');
      token = parts[parts.length - 1] || token;
    }
    token = token.split('?')[0].split('#')[0].replace(/\/+$/, '').trim();

    setLoading(true);
    setError(null);
    try {
      const classroom = await api.joinClassroom(token);
      if (onJoined) onJoined();
      onClose();
      navigate(`/classrooms/${classroom.id}`);
    } catch (err: any) {
      setError(err.message || 'Failed to join classroom');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
      <div className="w-full max-w-md rounded-3xl bg-olive-900 border border-olive-700 shadow-2xl p-6 sm:p-7 text-cream-100">
        <div className="flex items-center justify-between pb-4 border-b border-olive-700/80">
          <div className="flex items-center space-x-3">
            <div className="w-9 h-9 rounded-xl bg-cream-200 text-olive-950 flex items-center justify-center font-bold shadow-md">
              <Link2 className="w-4 h-4 text-olive-950" />
            </div>
            <div>
              <h3 className="text-lg font-display uppercase tracking-wider font-bold text-cream-200">
                Join Session
              </h3>
              <p className="text-[11px] text-olive-400">Enter classroom link or token</p>
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
              Classroom Link or Token *
            </label>
            <input
              type="text"
              required
              placeholder="Paste invitation link or token"
              value={tokenInput}
              onChange={(e) => setTokenInput(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition"
            />
          </div>

          <p className="text-xs text-olive-400 leading-relaxed">
            Joining grants you standard participant rights. You can upload assignments and receive your own private similarity report once the submission threshold is satisfied.
          </p>

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
              {loading ? 'Joining...' : 'Join Classroom'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
