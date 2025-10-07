import React, { useState } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { getUpstoxToken, clearUpstoxToken } from '../lib/auth';
import { isExpiredEOD } from '../lib/time';
import { apiClient } from '../lib/api';
import { SelectedInstrumentsSidebar } from './SelectedInstrumentsSidebar';
import { useSelectedInstruments } from '../queries/useInstruments';

export const ProtectedLayout: React.FC = () => {
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const { data: selectedInstruments = [] } = useSelectedInstruments();

  React.useEffect(() => {
    const token = getUpstoxToken();
    if (!token || isExpiredEOD(token.expiresAt)) {
      clearUpstoxToken();
      navigate('/login');
    }
  }, [navigate]);

  const logout = async () => {
    try { await apiClient.post('/api/session/logout'); } catch {}
    clearUpstoxToken();
    navigate('/login');
  };

  return (
    <div className="flex h-screen relative">
      {/* Floating Selected Instruments Button */}
      {selectedInstruments.length > 0 && (
        <button
          onClick={() => setSidebarOpen(true)}
          className="fixed right-4 bottom-4 z-30 bg-green-500 text-white p-3 rounded-full shadow-lg hover:bg-green-600 transition-colors"
          title="View Selected Instruments"
        >
          <div className="flex items-center">
            <span className="text-sm font-medium">{selectedInstruments.length}</span>
            <span className="ml-1">📈</span>
          </div>
        </button>
      )}
      
      <SelectedInstrumentsSidebar 
        isOpen={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
      />

      <aside className="w-56 bg-gray-900 text-gray-100 flex flex-col">
        <div className="p-4 font-semibold">Algo Trading</div>
        <nav className="flex-1 space-y-1 px-2">
          <NavLink to="/app/dashboard" className={({isActive})=>`block px-3 py-2 rounded text-sm ${isActive?'bg-gray-700':'hover:bg-gray-800'}`}>Dashboard</NavLink>
          <NavLink to="/app/trading" className={({isActive})=>`block px-3 py-2 rounded text-sm ${isActive?'bg-gray-700':'hover:bg-gray-800'}`}>Trading</NavLink>
          <NavLink to="/app/instruments" className={({isActive})=>`block px-3 py-2 rounded text-sm ${isActive?'bg-gray-700':'hover:bg-gray-800'}`}>Instruments</NavLink>
          <NavLink to="/app/market-data" className={({isActive})=>`block px-3 py-2 rounded text-sm ${isActive?'bg-gray-700':'hover:bg-gray-800'}`}>Market Data</NavLink>
          <NavLink to="/app/portfolio" className={({isActive})=>`block px-3 py-2 rounded text-sm ${isActive?'bg-gray-700':'hover:bg-gray-800'}`}>Portfolio</NavLink>
          <NavLink to="/app/strategies" className={({isActive})=>`block px-3 py-2 rounded text-sm ${isActive?'bg-gray-700':'hover:bg-gray-800'}`}>Strategies</NavLink>
        </nav>
        <button onClick={logout} className="m-2 rounded bg-red-600 hover:bg-red-700 text-sm py-2">Logout</button>
      </aside>
      <main className="flex-1 overflow-auto bg-gray-50">
        <Outlet />
      </main>
    </div>
  );
};
