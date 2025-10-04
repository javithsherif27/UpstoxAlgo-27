import React, { useState } from 'react';
import { saveUpstoxToken, getUpstoxToken, clearUpstoxToken } from '../lib/auth';
import { getEODIST } from '../lib/time';
import { useNavigate } from 'react-router-dom';
import { apiClient } from '../lib/api';

export const LoginPage: React.FC = () => {
  const [userId, setUserId] = useState('');
  const [accessToken, setAccessToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  React.useEffect(() => {
    const existing = getUpstoxToken();
    if (existing) {
      navigate('/app/dashboard');
    }
  }, [navigate]);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await apiClient.post('/api/session/login', { user_id: userId });
      saveUpstoxToken(accessToken, getEODIST());
      navigate('/app/dashboard');
    } catch (err: any) {
      setError(err?.message || 'Login failed');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <form onSubmit={submit} className="bg-white shadow rounded p-6 w-full max-w-md space-y-4">
        <h1 className="text-xl font-semibold">Algo Trading App Login</h1>
        <div>
          <label className="block text-sm font-medium mb-1">Upstox User ID</label>
          <input value={userId} onChange={e => setUserId(e.target.value)} required className="w-full border rounded px-3 py-2 text-sm" />
        </div>
        <div>
          <label className="block text-sm font-medium mb-1">Upstox Access Token</label>
          <input type="password" value={accessToken} onChange={e => setAccessToken(e.target.value)} required className="w-full border rounded px-3 py-2 text-sm" />
        </div>
        {error && <p className="text-sm text-red-600">{error}</p>}
        <button type="submit" className="w-full bg-blue-600 text-white rounded py-2 text-sm font-medium hover:bg-blue-700">Login</button>
      </form>
    </div>
  );
};
