import React, { useState, useEffect } from 'react';

function Dashboard() {
  const [status, setStatus] = useState(null);
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadData = async () => {
    try {
      const [statusResult, stocksResult] = await Promise.all([
        window.electronAPI.engine.getStatus(),
        window.electronAPI.stocks.list()
      ]);
      setStatus(statusResult);
      setStocks(stocksResult?.stocks || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleStart = async () => {
    try {
      await window.electronAPI.engine.start();
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleStop = async () => {
    try {
      await window.electronAPI.engine.stop();
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handlePause = async () => {
    try {
      await window.electronAPI.engine.pause();
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleResume = async () => {
    try {
      await window.electronAPI.engine.resume();
      loadData();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  const engineStatus = status?.status || 'stopped';
  const enabledStocks = status?.enabled_stocks || 0;
  const totalStocks = status?.total_stocks || 0;
  const tradeLogs = status?.recent_trades || [];

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>대시보드</h1>

      {error && <div className="error">{error}</div>}

      {/* 엔진 상태 */}
      <div className="card">
        <h2>엔진 상태</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
          <span className={`status-badge status-${engineStatus}`}>
            {engineStatus === 'running' ? '실행 중' :
             engineStatus === 'paused' ? '일시정지' : '정지'}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          {engineStatus === 'stopped' && (
            <button className="btn btn-success" onClick={handleStart}>시작</button>
          )}
          {engineStatus === 'running' && (
            <>
              <button className="btn btn-warning" onClick={handlePause}>일시정지</button>
              <button className="btn btn-danger" onClick={handleStop}>정지</button>
            </>
          )}
          {engineStatus === 'paused' && (
            <>
              <button className="btn btn-success" onClick={handleResume}>재개</button>
              <button className="btn btn-danger" onClick={handleStop}>정지</button>
            </>
          )}
        </div>
      </div>

      {/* 거래 통계 */}
      <div className="grid">
        <div className="metric-card">
          <h4>오늘 거래</h4>
          <div className="value">{status?.daily_trades || 0}회</div>
        </div>
        <div className="metric-card success">
          <h4>활성 종목</h4>
          <div className="value">{enabledStocks} / {totalStocks}개</div>
        </div>
        <div className="metric-card warning">
          <h4>모니터링 주기</h4>
          <div className="value">{status?.interval || 60}초</div>
        </div>
      </div>

      {/* 종목 현황 */}
      <div className="card">
        <h2>종목 현황</h2>
        <p style={{ color: 'var(--text-muted)', marginBottom: '1rem' }}>
          총 {totalStocks}개 종목 중 {enabledStocks}개 활성화됨
          {totalStocks === 0 && ' - 설정 페이지에서 종목을 추가하세요.'}
        </p>
        {stocks.length > 0 && (
          <table className="table">
            <thead>
              <tr>
                <th>상태</th>
                <th>종목코드</th>
                <th>종목명</th>
                <th>전략</th>
                <th>매수가/매도가</th>
              </tr>
            </thead>
            <tbody>
              {stocks.map((stock) => (
                <tr key={stock.code}>
                  <td>
                    <span className={`status-badge ${stock.enabled ? 'status-running' : 'status-stopped'}`}>
                      {stock.enabled ? '활성' : '비활성'}
                    </span>
                  </td>
                  <td>{stock.code}</td>
                  <td>{stock.name}</td>
                  <td>{stock.strategy === 'range_trading' ? '범위 매매' : '변동성 돌파'}</td>
                  <td>
                    {stock.strategy === 'range_trading'
                      ? `${stock.buy_price?.toLocaleString()} / ${stock.sell_price?.toLocaleString()}`
                      : `K=${stock.vb_params?.k || 0.5}`
                    }
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* 최근 거래 */}
      <div className="card">
        <h2>최근 거래</h2>
        {tradeLogs.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>시간</th>
                <th>종목</th>
                <th>구분</th>
                <th>가격</th>
                <th>수량</th>
              </tr>
            </thead>
            <tbody>
              {tradeLogs.slice(0, 5).map((log, idx) => (
                <tr key={idx}>
                  <td>{log.timestamp}</td>
                  <td>{log.stock_name}</td>
                  <td style={{ color: log.action === 'buy' ? '#ef4444' : '#3b82f6' }}>
                    {log.action === 'buy' ? '매수' : '매도'}
                  </td>
                  <td>{log.price?.toLocaleString()}원</td>
                  <td>{log.quantity}주</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>거래 내역이 없습니다.</p>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
