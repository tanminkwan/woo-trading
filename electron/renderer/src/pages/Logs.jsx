import React, { useState, useEffect } from 'react';

function Logs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadLogs();
  }, []);

  const loadLogs = async () => {
    try {
      const result = await window.electronAPI.logs.get(100);
      setLogs(result.logs || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>거래 로그</h1>
        <button className="btn btn-secondary" onClick={loadLogs}>새로고침</button>
      </div>

      {error && <div className="error">{error}</div>}

      <div className="card">
        {logs.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>시간</th>
                <th>종목</th>
                <th>구분</th>
                <th>가격</th>
                <th>수량</th>
                <th>금액</th>
                <th>사유</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, idx) => (
                <tr key={idx}>
                  <td>{log.timestamp}</td>
                  <td>{log.stock_name} ({log.stock_code})</td>
                  <td style={{
                    color: log.action === 'buy' ? '#ef4444' : '#3b82f6',
                    fontWeight: 600
                  }}>
                    {log.action === 'buy' ? '매수' : '매도'}
                  </td>
                  <td>{log.price?.toLocaleString()}원</td>
                  <td>{log.quantity}주</td>
                  <td>{(log.price * log.quantity)?.toLocaleString()}원</td>
                  <td>{log.reason || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: 'var(--text-muted)', textAlign: 'center', padding: '2rem' }}>
            거래 로그가 없습니다.
          </p>
        )}
      </div>
    </div>
  );
}

export default Logs;
