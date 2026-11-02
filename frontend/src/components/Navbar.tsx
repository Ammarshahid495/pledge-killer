import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, LayoutDashboard, LogOut, User as UserIcon, Plus, Link2 } from 'lucide-react';

export const Navbar: React.FC<{ onCreateClick?: () => void; onJoinClick?: () => void }> = ({
  onCreateClick,
  onJoinClick,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return (
    <header className="sticky top-0 z-40 w-full border-b border-olive-700 bg-olive-950/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 py-3.5 flex items-center justify-between">
        <Link to="/" className="flex items-center space-x-3 group">
          <div className="w-10 h-10 rounded-2xl bg-cream-200 text-olive-950 flex items-center justify-center font-bold shadow-lg shadow-cream-200/10 group-hover:scale-105 transition-transform">
            <Shield className="w-5 h-5 text-olive-950" />
          </div>
          <div>
            <span className="text-xl font-display uppercase tracking-wider font-extrabold text-cream-100 flex items-center gap-1.5">
              PLEDGE <span className="text-cream-300">FIGHTER</span>
            </span>
            <span className="text-[9px] text-olive-400 block -mt-1 tracking-widest uppercase font-semibold">
              Peer-to-Peer Privacy
            </span>
          </div>
        </Link>

        {user ? (
          <div className="flex items-center space-x-3 sm:space-x-5">
            <Link
              to="/dashboard"
              className="text-xs font-bold uppercase tracking-wider text-olive-300 hover:text-cream-200 flex items-center space-x-1.5 transition-colors"
            >
              <LayoutDashboard className="w-4 h-4" />
              <span className="hidden sm:inline">Dashboard</span>
            </Link>

            <div className="flex items-center space-x-2">
              {onCreateClick && (
                <button
                  onClick={onCreateClick}
                  className="px-4 py-2 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-bold uppercase tracking-wider flex items-center space-x-1.5 transition shadow-md shadow-cream-200/10"
                >
                  <Plus className="w-3.5 h-3.5 stroke-[2.5]" />
                  <span>Create</span>
                </button>
              )}
              {onJoinClick && (
                <button
                  onClick={onJoinClick}
                  className="px-4 py-2 rounded-full bg-olive-850 hover:bg-olive-800 text-cream-200 text-xs font-bold uppercase tracking-wider border border-olive-700 transition"
                >
                  Join Link
                </button>
              )}
            </div>

            <div className="h-5 w-px bg-olive-700" />

            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2 text-xs">
                <div className="w-8 h-8 rounded-full bg-olive-800 border border-olive-700 flex items-center justify-center text-cream-200 font-bold">
                  <UserIcon className="w-4 h-4" />
                </div>
                <span className="hidden md:inline font-semibold text-cream-200">{user.display_name}</span>
              </div>
              <button
                onClick={handleLogout}
                title="Log out"
                className="p-2 rounded-xl text-olive-400 hover:text-rose-400 hover:bg-olive-800 transition"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          </div>
        ) : (
          <div className="flex items-center space-x-4">
            <Link
              to="/login"
              className="text-xs font-bold uppercase tracking-wider text-olive-300 hover:text-cream-200 transition-colors"
            >
              Sign In
            </Link>
            <Link
              to="/register"
              className="px-5 py-2.5 rounded-full bg-cream-200 hover:bg-cream-100 text-olive-950 text-xs font-bold uppercase tracking-wider shadow-lg shadow-cream-200/15 transition-all hover:scale-105"
            >
              Get Started
            </Link>
          </div>
        )}
      </div>
    </header>
  );
};
