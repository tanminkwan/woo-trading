import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

function Backtest() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [result, setResult] = useState(null);

  const [form, setForm] = useState({
    stock_code: '',
    stock_name: '',
    start_date: getDefaultStartDate(),
    end_date: getDefaultEndDate(),
    capital: 1000000,
    strategy: 'range_trading',
    use_mock: true,
    use_minute_data: false,
    buy_price: 0,
    sell_price: 0,
    k: 0.5,
    target_profit_rate: 2.0,
    stop_loss_rate: -2.0,
  });

  function getDefaultStartDate() {
    const date = new Date();
    date.setMonth(date.getMonth() - 1);
    return date.toISOString().split('T')[0];
  }

  function getDefaultEndDate() {
    return new Date().toISOString().split('T')[0];
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const params = {
        ...form,
        start_date: form.start_date.replace(/-/g, ''),
        end_date: form.end_date.replace(/-/g, ''),
      };

      const response = await window.electronAPI.backtest.run(params);

      if (response.success) {
        setResult(response.data);
      } else {
        setError(response.message || '백테스트 실행 실패');
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    if (dateStr.length === 14) {
      return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)} ${dateStr.slice(8, 10)}:${dateStr.slice(10, 12)}`;
    }
    if (dateStr.length === 8) {
      return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
    }
    return dateStr;
  };

  const getChartData = () => {
    if (!result?.price_data) return null;

    const priceData = result.price_data;
    const trades = result.trades || [];
    const useMinuteData = result.use_minute_data;

    // 샘플링
    let displayData = priceData;
    if (priceData.length > 500) {
      const rate = Math.ceil(priceData.length / 500);
      displayData = priceData.filter((_, idx) => idx % rate === 0);
    }

    const labels = displayData.map(d =>
      useMinuteData && d.time ? `${formatDate(d.date)} ${d.time}` : formatDate(d.date)
    );
    const prices = displayData.map(d => d.close_price);

    const buyPoints = new Array(displayData.length).fill(null);
    const sellPoints = new Array(displayData.length).fill(null);

    trades.forEach(trade => {
      const idx = useMinuteData
        ? displayData.findIndex(d => d.datetime >= trade.date)
        : displayData.findIndex(d => d.date === trade.date);

      if (idx !== -1) {
        if (trade.trade_type === 'buy') {
          buyPoints[idx] = trade.price;
        } else {
          sellPoints[idx] = trade.price;
        }
      }
    });

    return {
      labels,
      datasets: [
        {
          label: '종가',
          data: prices,
          borderColor: '#3b82f6',
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
          borderWidth: 2,
          fill: true,
          tension: 0.1,
          pointRadius: 0,
        },
        {
          label: '매수',
          data: buyPoints,
          borderColor: '#ef4444',
          backgroundColor: '#ef4444',
          pointRadius: 8,
          pointStyle: 'triangle',
          showLine: false,
        },
        {
          label: '매도',
          data: sellPoints,
          borderColor: '#10b981',
          backgroundColor: '#10b981',
          pointRadius: 8,
          pointStyle: 'rectRot',
          showLine: false,
        },
      ],
    };
  };

  return (
    <div>
      <h1 style={{ marginBottom: '1.5rem' }}>백테스트</h1>

      {error && <div className="error">{error}</div>}

      {/* 설정 폼 */}
      <div className="card">
        <h2>백테스트 설정</h2>
        <div style={{
          backgroundColor: '#fef3c7',
          border: '1px solid #f59e0b',
          borderRadius: '0.375rem',
          padding: '0.75rem 1rem',
          marginBottom: '1rem',
          fontSize: '0.875rem',
          color: '#92400e'
        }}>
          <strong>참고:</strong> 실제 API는 당일 분봉 데이터만 제공합니다. 과거 데이터 백테스트 시 "일봉"을 사용하거나, 분봉 시뮬레이션은 "Mock 데이터"를 선택하세요.
        </div>
        <form onSubmit={handleSubmit}>
          <div className="form-row">
            <div className="form-group">
              <label>종목코드 *</label>
              <input
                type="text"
                value={form.stock_code}
                onChange={(e) => setForm({ ...form, stock_code: e.target.value })}
                placeholder="005930"
                required
              />
            </div>
            <div className="form-group">
              <label>종목명</label>
              <input
                type="text"
                value={form.stock_name}
                onChange={(e) => setForm({ ...form, stock_name: e.target.value })}
                placeholder="삼성전자"
              />
            </div>
            <div className="form-group">
              <label>초기 자본금</label>
              <input
                type="number"
                value={form.capital}
                onChange={(e) => setForm({ ...form, capital: parseInt(e.target.value) })}
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>시작일</label>
              <input
                type="date"
                value={form.start_date}
                onChange={(e) => setForm({ ...form, start_date: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>종료일</label>
              <input
                type="date"
                value={form.end_date}
                onChange={(e) => setForm({ ...form, end_date: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label>전략</label>
              <select
                value={form.strategy}
                onChange={(e) => setForm({ ...form, strategy: e.target.value })}
              >
                <option value="range_trading">범위 매매</option>
                <option value="volatility_breakout">변동성 돌파</option>
              </select>
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label>데이터 소스</label>
              <select
                value={form.use_mock ? 'true' : 'false'}
                onChange={(e) => setForm({ ...form, use_mock: e.target.value === 'true' })}
              >
                <option value="true">Mock 데이터</option>
                <option value="false">실제 API</option>
              </select>
            </div>
            <div className="form-group">
              <label>데이터 단위</label>
              <select
                value={form.use_minute_data ? 'true' : 'false'}
                onChange={(e) => setForm({ ...form, use_minute_data: e.target.value === 'true' })}
              >
                <option value="false">일봉</option>
                <option value="true">분봉</option>
              </select>
            </div>
          </div>

          {form.strategy === 'range_trading' && (
            <div className="form-row">
              <div className="form-group">
                <label>매수가</label>
                <input
                  type="number"
                  value={form.buy_price}
                  onChange={(e) => setForm({ ...form, buy_price: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div className="form-group">
                <label>매도가</label>
                <input
                  type="number"
                  value={form.sell_price}
                  onChange={(e) => setForm({ ...form, sell_price: parseInt(e.target.value) || 0 })}
                />
              </div>
            </div>
          )}

          {form.strategy === 'volatility_breakout' && (
            <div className="form-row">
              <div className="form-group">
                <label>K값</label>
                <input
                  type="number"
                  step="0.1"
                  value={form.k}
                  onChange={(e) => setForm({ ...form, k: parseFloat(e.target.value) })}
                />
              </div>
              <div className="form-group">
                <label>목표 수익률 (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={form.target_profit_rate}
                  onChange={(e) => setForm({ ...form, target_profit_rate: parseFloat(e.target.value) })}
                />
              </div>
              <div className="form-group">
                <label>손절 수익률 (%)</label>
                <input
                  type="number"
                  step="0.1"
                  value={form.stop_loss_rate}
                  onChange={(e) => setForm({ ...form, stop_loss_rate: parseFloat(e.target.value) })}
                />
              </div>
            </div>
          )}

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '실행 중...' : '백테스트 실행'}
          </button>
        </form>
      </div>

      {/* 결과 */}
      {result && (
        <>
          <div className="grid">
            <div className={`metric-card ${result.total_return_rate >= 0 ? 'success' : 'danger'}`}>
              <h4>수익률</h4>
              <div className="value">
                {result.total_return_rate >= 0 ? '+' : ''}{result.total_return_rate.toFixed(2)}%
              </div>
            </div>
            <div className="metric-card">
              <h4>총 거래</h4>
              <div className="value">{result.total_trades}회</div>
            </div>
            <div className={`metric-card ${result.win_rate >= 50 ? 'success' : 'warning'}`}>
              <h4>승률</h4>
              <div className="value">{result.win_rate.toFixed(1)}%</div>
            </div>
            <div className="metric-card danger">
              <h4>최대 낙폭</h4>
              <div className="value">{result.max_drawdown.toFixed(2)}%</div>
            </div>
          </div>

          {/* 차트 */}
          <div className="card">
            <h2>가격 차트</h2>
            <div className="chart-container">
              {getChartData() && (
                <Line
                  data={getChartData()}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                      x: { display: true, ticks: { maxTicksLimit: 10 } },
                      y: {
                        display: true,
                        ticks: {
                          callback: (value) => value.toLocaleString() + '원'
                        }
                      }
                    }
                  }}
                />
              )}
            </div>
          </div>

          {/* 거래 내역 */}
          <div className="card">
            <h2>거래 내역</h2>
            {result.trades?.length > 0 ? (
              <table className="table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>일자</th>
                    <th>구분</th>
                    <th>가격</th>
                    <th>수량</th>
                    <th>손익</th>
                    <th>사유</th>
                  </tr>
                </thead>
                <tbody>
                  {result.trades.map((trade, idx) => (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      <td>{formatDate(trade.date)}</td>
                      <td style={{
                        color: trade.trade_type === 'buy' ? '#ef4444' : '#3b82f6',
                        fontWeight: 600
                      }}>
                        {trade.trade_type === 'buy' ? '매수' : '매도'}
                      </td>
                      <td>{trade.price.toLocaleString()}원</td>
                      <td>{trade.quantity}주</td>
                      <td style={{
                        color: trade.profit_loss > 0 ? '#ef4444' : trade.profit_loss < 0 ? '#3b82f6' : 'inherit'
                      }}>
                        {trade.profit_loss !== 0
                          ? `${trade.profit_loss > 0 ? '+' : ''}${trade.profit_loss.toLocaleString()}원 (${trade.profit_rate.toFixed(2)}%)`
                          : '-'
                        }
                      </td>
                      <td>{trade.reason}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>거래 내역이 없습니다.</p>
            )}
          </div>
        </>
      )}
    </div>
  );
}

export default Backtest;
