import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { register } from '../api/auth';
import { login } from '../api/auth';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await register(email, password);
      await login(email, password);
      navigate('/');
      window.location.reload();
    } catch {
      setError('Registrering feilet. E-posten kan allerede vaere i bruk.');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full bg-white rounded-lg shadow-md p-8">
        <h1 className="text-2xl font-bold text-center text-blue-700 mb-6">Jobbsok</h1>
        <h2 className="text-lg font-semibold text-center mb-4">Registrer deg</h2>
        {error && <p className="text-red-600 text-sm text-center mb-4">{error}</p>}
        <form onSubmit={handleSubmit} className="space-y-4">
          <input
            type="email" placeholder="E-post" value={email}
            onChange={(e) => setEmail(e.target.value)} required
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <input
            type="password" placeholder="Passord" value={password}
            onChange={(e) => setPassword(e.target.value)} required minLength={6}
            className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          />
          <button type="submit" className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700">
            Registrer
          </button>
        </form>
        <p className="text-center text-sm text-gray-500 mt-4">
          Har du allerede konto? <Link to="/login" className="text-blue-600 hover:underline">Logg inn</Link>
        </p>
      </div>
    </div>
  );
}
