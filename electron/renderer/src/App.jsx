import React from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Config from './pages/Config';
import Logs from './pages/Logs';
import Backtest from './pages/Backtest';

function App() {
  return (
    <div className="app">
      <nav className="sidebar">
        <div className="logo">
          <h1>AutoStock</h1>
        </div>
        <ul className="nav-menu">
          <li>
            <NavLink to="/" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="icon">📊</span>
              <span>대시보드</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/config" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="icon">⚙️</span>
              <span>설정</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/logs" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="icon">📋</span>
              <span>거래 로그</span>
            </NavLink>
          </li>
          <li>
            <NavLink to="/backtest" className={({ isActive }) => isActive ? 'active' : ''}>
              <span className="icon">📈</span>
              <span>백테스트</span>
            </NavLink>
          </li>
        </ul>
      </nav>
      <main className="content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/config" element={<Config />} />
          <Route path="/logs" element={<Logs />} />
          <Route path="/backtest" element={<Backtest />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;
