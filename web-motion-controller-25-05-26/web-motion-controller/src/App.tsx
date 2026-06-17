import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import Layout from './components/Layout/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import AxisControl from './pages/AxisControl';
import Monitoring from './pages/Monitoring';
import Alarms from './pages/Alarms';
import AuditLog from './pages/AuditLog';
import './index.css';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const user = useAuthStore(s => s.user);
  return user ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<PrivateRoute><Layout /></PrivateRoute>}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard" element={<Dashboard />} />
          <Route path="axis-control" element={<AxisControl />} />
          <Route path="monitoring" element={<Monitoring />} />
          <Route path="alarms" element={<Alarms />} />
          <Route path="audit-log" element={<AuditLog />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
