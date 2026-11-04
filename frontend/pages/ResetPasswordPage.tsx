import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { api } from '../api/client';
import { Navbar } from '../components/Navbar';
import { Shield, AlertCircle, ArrowRight, CheckCircle2 } from 'lucide-react';

export const ResetPasswordPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const token = new URLSearchParams(location.search).get('token') || '';

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await api.resetPassword(token, password, confirmPassword);
      setDone(true);
    } catch (err: any) {
      setError(err.message || 'Could not reset the password');
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    'w-full px-4 py-3 rounded-2xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition';

  return (
    <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
      <Navbar />

      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md rounded-3xl bg-olive-900 border border-olive-700 shadow-2xl p-8 sm:p-9 text-cream-100">
          {done ? (
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-cream-200 text-olive-950 mx-auto flex items-center justify-center shadow-md">
                <CheckCircle2 className="w-6 h-6 text-olive-950" />
              </div>
              <h2 className="text-2xl font-display font-bold uppercase tracking-wider text-cream-200">
                Password Updated
              </h2>
              <p className="text-xs text-olive-300 leading-relaxed">
                Your password was changed. You were signed out everywhere, so sign in again with the new one.
              </p>
              <button
                onClick={() => navigate('/login')}
                className="w-full mt-2 py-3.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-display font-bold uppercase tracking-wider shadow-lg shadow-cream-200/15 transition"
              >
                SIGN IN
              </button>
            </div>
          ) : !token ? (
            <div className="text-center space-y-4">
              <div className="w-12 h-12 rounded-2xl bg-rose-500/10 mx-auto flex items-center justify-center">
                <AlertCircle className="w-6 h-6 text-rose-300" />
              </div>
              <h2 className="text-2xl font-display font-bold uppercase tracking-wider text-cream-200">
                Invalid Link
              </h2>
              <p className="text-xs text-olive-300 leading-relaxed">
                This reset link is missing its token. Request a new link and use the one in the latest email.
              </p>
              <Link
                to="/forgot-password"
                className="inline-block text-xs font-bold uppercase tracking-wider text-cream-200 hover:text-cream-100"
              >
                Request a New Link
              </Link>
            </div>
          ) : (
            <>
              <div className="text-center mb-8">
                <div className="w-12 h-12 rounded-2xl bg-cream-200 text-olive-950 mx-auto flex items-center justify-center mb-4 font-bold shadow-md">
                  <Shield className="w-6 h-6 text-olive-950" />
                </div>
                <h2 className="text-2xl font-display font-bold uppercase tracking-wider text-cream-200">
                  New Password
                </h2>
                <p className="text-xs text-olive-400 mt-1">Choose a new password for your account</p>
              </div>

              {error && (
                <div className="mb-6 p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs space-y-2">
                  <div className="flex items-center space-x-2">
                    <AlertCircle className="w-4 h-4 shrink-0" />
                    <span>{error}</span>
                  </div>
                  <Link
                    to="/forgot-password"
                    className="inline-block font-bold uppercase tracking-wider text-cream-200 hover:text-cream-100"
                  >
                    Request a new link
                  </Link>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                    New Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    placeholder="At least 8 characters"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={inputClass}
                  />
                </div>

                <div>
                  <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    required
                    placeholder="Repeat the new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={inputClass}
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full mt-3 py-3.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-display font-bold uppercase tracking-wider shadow-lg shadow-cream-200/15 transition flex items-center justify-center space-x-2 disabled:opacity-50"
                >
                  <span>{loading ? 'SAVING...' : 'UPDATE PASSWORD'}</span>
                  <ArrowRight className="w-4 h-4 stroke-[2.5]" />
                </button>
              </form>
            </>
          )}
        </div>
      </div>
    </div>
  );
};
