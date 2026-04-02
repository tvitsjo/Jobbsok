import { Routes, Route, Navigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getMe } from './api/auth';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import PreferencesPage from './pages/PreferencesPage';
import JobResultsPage from './pages/JobResultsPage';
import JobDetailPage from './pages/JobDetailPage';
import AdminDashboard from './pages/admin/AdminDashboard';
import Navbar from './components/layout/Navbar';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('access_token');
  if (!token) return <Navigate to="/login" />;
  return <>{children}</>;
}

export default function App() {
  const { data: user } = useQuery({
    queryKey: ['me'],
    queryFn: () => getMe().then((r) => r.data),
    enabled: !!localStorage.getItem('access_token'),
    retry: false,
  });

  return (
    <div className="min-h-screen bg-gray-50">
      {user && <Navbar user={user} />}
      <main className={user ? 'pt-16' : ''}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/profile" element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/preferences" element={<ProtectedRoute><PreferencesPage /></ProtectedRoute>} />
          <Route path="/jobs" element={<ProtectedRoute><JobResultsPage /></ProtectedRoute>} />
          <Route path="/jobs/:id" element={<ProtectedRoute><JobDetailPage /></ProtectedRoute>} />
          {user?.is_admin && (
            <Route path="/admin" element={<ProtectedRoute><AdminDashboard /></ProtectedRoute>} />
          )}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </main>
    </div>
  );
}
