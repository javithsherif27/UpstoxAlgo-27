import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { InstrumentsPage } from './pages/InstrumentsPage';
import { MarketDataPage } from './pages/MarketDataPage';
import { StrategiesPage } from './pages/StrategiesPage';
import { ProtectedLayout } from './components/ProtectedLayout';

export const AppRouter: React.FC = () => {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/app" element={<ProtectedLayout />}> 
        <Route path="dashboard" element={<DashboardPage />} />
        <Route path="instruments" element={<InstrumentsPage />} />
        <Route path="market-data" element={<MarketDataPage />} />
        <Route path="strategies" element={<StrategiesPage />} />
        <Route index element={<Navigate to="dashboard" replace />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
};
