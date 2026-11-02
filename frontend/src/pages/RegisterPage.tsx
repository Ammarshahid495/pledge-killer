import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import { Shield, AlertCircle, ArrowRight } from 'lucide-react';

export const RegisterPage: React.FC = () => {
  const [displayName, setDisplayName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { register } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const redirectUrl = searchParams.get('redirect');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await register({
        display_name: displayName,
        email,
        password,
        confirm_password: confirmPassword,
      });
      navigate(redirectUrl || '/dashboard');
    } catch (err: any) {
      setError(err.message || 'Registration failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-olive-950 text-cream-100 flex flex-col">
      <Navbar />

      <div className="flex-1 flex items-center justify-center p-4">
        <div className="w-full max-w-md rounded-3xl bg-olive-900 border border-olive-700 shadow-2xl p-8 sm:p-9 text-cream-100">
          <div className="text-center mb-8">
            <div className="w-12 h-12 rounded-2xl bg-cream-200 text-olive-950 mx-auto flex items-center justify-center mb-4 font-bold shadow-md">
              <Shield className="w-6 h-6 text-olive-950" />
            </div>
            <h2 className="text-2xl font-display font-bold uppercase tracking-wider text-cream-200">Create Account</h2>
            <p className="text-xs text-olive-400 mt-1">Equal participant permissions by default</p>
          </div>

          {error && (
            <div className="mb-6 p-3.5 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                Display Name
              </label>
              <input
                type="text"
                required
                placeholder="e.g. Alex Taylor"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                Email Address
              </label>
              <input
                type="email"
                required
                placeholder="student@university.edu"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                Password (min 8 chars)
              </label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition"
              />
            </div>

            <div>
              <label className="block text-[11px] font-semibold text-olive-300 mb-1.5 uppercase tracking-wider">
                Confirm Password
              </label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-4 py-3 rounded-2xl bg-olive-850 border border-olive-700 text-cream-100 placeholder-olive-500 text-sm focus:outline-none focus:border-cream-200 transition"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-3 py-3.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-display font-bold uppercase tracking-wider shadow-lg shadow-cream-200/15 transition flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'REGISTERING...' : 'REGISTER'}</span>
              <ArrowRight className="w-4 h-4 stroke-[2.5]" />
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-olive-700/80 text-center text-xs text-olive-400">
            Already registered?{' '}
            <Link to="/login" className="text-cream-200 hover:text-cream-100 font-bold uppercase tracking-wider ml-1">
              Sign In
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
