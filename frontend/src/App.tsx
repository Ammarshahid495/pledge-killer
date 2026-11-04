import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useParams, useNavigate, Link } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { LandingPage } from './pages/LandingPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { ForgotPasswordPage } from './pages/ForgotPasswordPage';
import { ResetPasswordPage } from './pages/ResetPasswordPage';
import { DashboardPage } from './pages/DashboardPage';
import { ClassroomPage } from './pages/ClassroomPage';
import { ReportPage } from './pages/ReportPage';
import { api } from './api/client';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading } = useAuth();
  if (loading) {
    return <div className="min-h-screen bg-dark-900 flex items-center justify-center text-slate-400">Loading...</div>;
  }
  if (!user) {
    return <Navigate to="/login" replace />;
  }
  return <>{children}</>;
};

const JoinHandler: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const { user, loading } = useAuth();
  const [error, setError] = React.useState<string | null>(null);
  const [joining, setJoining] = React.useState(false);
  const navigate = useNavigate();

  React.useEffect(() => {
    if (!loading && user && token && !joining) {
      setJoining(true);
      api.joinClassroom(token)
        .then((c) => {
          navigate(`/classrooms/${c.id}`, { replace: true });
        })
        .catch((err) => {
          setError(err.message || 'Failed to join classroom');
          setJoining(false);
        });
    }
  }, [loading, user, token, joining]);

  if (loading) {
    return <div className="min-h-screen bg-olive-950 flex items-center justify-center text-olive-400 text-xs uppercase tracking-widest">Verifying link...</div>;
  }

  if (!user) {
    return <Navigate to={`/login?redirect=/join/${token}`} replace />;
  }

  if (error) {
    return (
      <div className="min-h-screen bg-olive-950 flex items-center justify-center text-cream-100 p-4">
        <div className="max-w-md p-8 rounded-3xl bg-olive-900 border border-olive-700 text-center space-y-3">
          <h2 className="text-lg font-display font-bold uppercase text-rose-400">Join Failed</h2>
          <p className="text-xs text-olive-400">{error}</p>
          <div className="pt-2">
            <Link to="/dashboard" className="px-5 py-2.5 rounded-full bg-cream-200 text-olive-950 text-xs font-bold uppercase tracking-wider inline-block">
              Go to Dashboard
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-olive-950 flex items-center justify-center text-cream-200 font-display text-sm uppercase tracking-wider">
      Joining classroom...
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/join/:token" element={<JoinHandler />} />

          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/classrooms/:id"
            element={
              <ProtectedRoute>
                <ClassroomPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/reports/:reportId"
            element={
              <ProtectedRoute>
                <ReportPage />
              </ProtectedRoute>
            }
          />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
