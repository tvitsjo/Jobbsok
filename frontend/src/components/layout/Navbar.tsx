import { Link, useNavigate } from 'react-router-dom';
import { logout } from '../../api/auth';
import type { User } from '../../types';

export default function Navbar({ user }: { user: User }) {
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
    window.location.reload();
  };

  return (
    <nav className="fixed top-0 left-0 right-0 bg-white border-b border-gray-200 z-50">
      <div className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
        <div className="flex items-center gap-8">
          <Link to="/" className="text-xl font-bold text-blue-700">Jobbsok</Link>
          <div className="flex gap-4">
            <Link to="/" className="text-gray-600 hover:text-gray-900">Dashboard</Link>
            <Link to="/profile" className="text-gray-600 hover:text-gray-900">Profil</Link>
            <Link to="/preferences" className="text-gray-600 hover:text-gray-900">Preferanser</Link>
            <Link to="/jobs" className="text-gray-600 hover:text-gray-900">Jobber</Link>
            {user.is_admin && (
              <Link to="/admin" className="text-gray-600 hover:text-gray-900">Admin</Link>
            )}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-gray-500">{user.email}</span>
          <button onClick={handleLogout} className="text-sm text-red-600 hover:text-red-800">
            Logg ut
          </button>
        </div>
      </div>
    </nav>
  );
}
