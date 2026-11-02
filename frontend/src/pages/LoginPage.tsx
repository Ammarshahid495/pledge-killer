import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Navbar } from '../components/Navbar';
import { Shield, AlertCircle, ArrowRight } from 'lucide-react';

export const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const searchParams = new URLSearchParams(location.search);
  const redirectUrl = searchParams.get('redirect');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await login({ email, password });
      navigate(redirectUrl || '/dashboard');
    } catch (err: any) {
      setError(err.message || 'Invalid email or password');
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
            <h2 className="text-2xl font-display font-bold uppercase tracking-wider text-cream-200">Welcome Back</h2>
            <p className="text-xs text-olive-400 mt-1">Sign in to your peer similarity sessions</p>
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
                Password
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

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-3 py-3.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-display font-bold uppercase tracking-wider shadow-lg shadow-cream-200/15 transition flex items-center justify-center space-x-2 disabled:opacity-50"
            >
              <span>{loading ? 'AUTHENTICATING...' : 'SIGN IN'}</span>
              <ArrowRight className="w-4 h-4 stroke-[2.5]" />
            </button>
          </form>

          <div className="mt-8 pt-6 border-t border-olive-700/80 text-center text-xs text-olive-400">
            Need an account?{' '}
            <Link
              to={redirectUrl ? `/register?redirect=${encodeURIComponent(redirectUrl)}` : "/register"}
              className="text-cream-200 hover:text-cream-100 font-bold uppercase tracking-wider ml-1"
            >
              Register Here
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
