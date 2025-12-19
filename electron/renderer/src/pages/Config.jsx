import React, { useState, useEffect } from 'react';

function Config() {
  const [stocks, setStocks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingStock, setEditingStock] = useState(null);
  const [newStock, setNewStock] = useState({
    code: '',
    name: '',
    strategy: 'range_trading',
    max_amount: 1000000,
    buy_price: 0,
    sell_price: 0,
    k: 0.5,
    target_profit_rate: 2.0,
    stop_loss_rate: -2.0,
    enabled: true,
  });

  useEffect(() => {
    loadStocks();
  }, []);

  const loadStocks = async () => {
    try {
      const result = await window.electronAPI.stocks.list();
      setStocks(result.stocks || []);
      setError(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (code) => {
    try {
      await window.electronAPI.stocks.toggle(code);
      loadStocks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleDelete = async (code) => {
    if (!confirm('정말 삭제하시겠습니까?')) return;
    try {
      await window.electronAPI.stocks.delete(code);
      loadStocks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await window.electronAPI.stocks.add(newStock);
      setShowAddForm(false);
      setNewStock({
        code: '',
        name: '',
        strategy: 'range_trading',
        max_amount: 1000000,
        buy_price: 0,
        sell_price: 0,
        k: 0.5,
        target_profit_rate: 2.0,
        stop_loss_rate: -2.0,
        enabled: true,
      });
      loadStocks();
    } catch (err) {
      setError(err.message);
    }
  };

  const handleEdit = (stock) => {
    setEditingStock({
      ...stock,
      k: stock.vb_params?.k || 0.5,
      target_profit_rate: stock.vb_params?.target_profit_rate || 2.0,
      stop_loss_rate: stock.vb_params?.stop_loss_rate || -2.0,
    });
    setShowAddForm(false);
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    try {
      await window.electronAPI.stocks.update(editingStock.code, editingStock);
      setEditingStock(null);
      loadStocks();
    } catch (err) {
      setError(err.message);
    }
  };

  if (loading) {
    return <div className="loading">로딩 중...</div>;
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1>종목 설정</h1>
        <button className="btn btn-primary" onClick={() => setShowAddForm(!showAddForm)}>
          {showAddForm ? '취소' : '+ 종목 추가'}
        </button>
      </div>

      {error && <div className="error">{error}</div>}

      {/* 종목 추가 폼 */}
      {showAddForm && (
        <div className="card">
          <h2>새 종목 추가</h2>
          <form onSubmit={handleAdd}>
            <div className="form-row">
              <div className="form-group">
                <label>종목코드 *</label>
                <input
                  type="text"
                  value={newStock.code}
                  onChange={(e) => setNewStock({ ...newStock, code: e.target.value })}
                  placeholder="005930"
                  required
                />
              </div>
              <div className="form-group">
                <label>종목명</label>
                <input
                  type="text"
                  value={newStock.name}
                  onChange={(e) => setNewStock({ ...newStock, name: e.target.value })}
                  placeholder="삼성전자"
                />
              </div>
              <div className="form-group">
                <label>전략</label>
                <select
                  value={newStock.strategy}
                  onChange={(e) => setNewStock({ ...newStock, strategy: e.target.value })}
                >
                  <option value="range_trading">범위 매매</option>
                  <option value="volatility_breakout">변동성 돌파</option>
                </select>
              </div>
              <div className="form-group">
                <label>최대 투자금액</label>
                <input
                  type="number"
                  value={newStock.max_amount}
                  onChange={(e) => setNewStock({ ...newStock, max_amount: parseInt(e.target.value) })}
                />
              </div>
            </div>

            {newStock.strategy === 'range_trading' && (
              <div className="form-row">
                <div className="form-group">
                  <label>매수가</label>
                  <input
                    type="number"
                    value={newStock.buy_price}
                    onChange={(e) => setNewStock({ ...newStock, buy_price: parseInt(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>매도가</label>
                  <input
                    type="number"
                    value={newStock.sell_price}
                    onChange={(e) => setNewStock({ ...newStock, sell_price: parseInt(e.target.value) })}
                  />
                </div>
              </div>
            )}

            {newStock.strategy === 'volatility_breakout' && (
              <div className="form-row">
                <div className="form-group">
                  <label>K값</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newStock.k}
                    onChange={(e) => setNewStock({ ...newStock, k: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>목표 수익률 (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newStock.target_profit_rate}
                    onChange={(e) => setNewStock({ ...newStock, target_profit_rate: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>손절 수익률 (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={newStock.stop_loss_rate}
                    onChange={(e) => setNewStock({ ...newStock, stop_loss_rate: parseFloat(e.target.value) })}
                  />
                </div>
              </div>
            )}

            <button type="submit" className="btn btn-primary">추가</button>
          </form>
        </div>
      )}

      {/* 종목 수정 폼 */}
      {editingStock && (
        <div className="card">
          <h2>종목 수정: {editingStock.name} ({editingStock.code})</h2>
          <form onSubmit={handleUpdate}>
            <div className="form-row">
              <div className="form-group">
                <label>종목명</label>
                <input
                  type="text"
                  value={editingStock.name}
                  onChange={(e) => setEditingStock({ ...editingStock, name: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>전략</label>
                <select
                  value={editingStock.strategy}
                  onChange={(e) => setEditingStock({ ...editingStock, strategy: e.target.value })}
                >
                  <option value="range_trading">범위 매매</option>
                  <option value="volatility_breakout">변동성 돌파</option>
                </select>
              </div>
              <div className="form-group">
                <label>최대 투자금액</label>
                <input
                  type="number"
                  value={editingStock.max_amount}
                  onChange={(e) => setEditingStock({ ...editingStock, max_amount: parseInt(e.target.value) })}
                />
              </div>
            </div>

            {editingStock.strategy === 'range_trading' && (
              <div className="form-row">
                <div className="form-group">
                  <label>매수가</label>
                  <input
                    type="number"
                    value={editingStock.buy_price}
                    onChange={(e) => setEditingStock({ ...editingStock, buy_price: parseInt(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>매도가</label>
                  <input
                    type="number"
                    value={editingStock.sell_price}
                    onChange={(e) => setEditingStock({ ...editingStock, sell_price: parseInt(e.target.value) })}
                  />
                </div>
              </div>
            )}

            {editingStock.strategy === 'volatility_breakout' && (
              <div className="form-row">
                <div className="form-group">
                  <label>K값</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingStock.k}
                    onChange={(e) => setEditingStock({ ...editingStock, k: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>목표 수익률 (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingStock.target_profit_rate}
                    onChange={(e) => setEditingStock({ ...editingStock, target_profit_rate: parseFloat(e.target.value) })}
                  />
                </div>
                <div className="form-group">
                  <label>손절 수익률 (%)</label>
                  <input
                    type="number"
                    step="0.1"
                    value={editingStock.stop_loss_rate}
                    onChange={(e) => setEditingStock({ ...editingStock, stop_loss_rate: parseFloat(e.target.value) })}
                  />
                </div>
              </div>
            )}

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button type="submit" className="btn btn-primary">저장</button>
              <button type="button" className="btn btn-secondary" onClick={() => setEditingStock(null)}>취소</button>
            </div>
          </form>
        </div>
      )}

      {/* 종목 목록 */}
      <div className="card">
        <h2>등록된 종목</h2>
        {stocks.length > 0 ? (
          <table className="table">
            <thead>
              <tr>
                <th>활성</th>
                <th>종목코드</th>
                <th>종목명</th>
                <th>전략</th>
                <th>매수가/매도가</th>
                <th>최대금액</th>
                <th>작업</th>
              </tr>
            </thead>
            <tbody>
              {stocks.map((stock) => (
                <tr key={stock.code}>
                  <td>
                    <div
                      onClick={() => handleToggle(stock.code)}
                      style={{
                        width: '44px',
                        height: '24px',
                        backgroundColor: stock.enabled ? '#10b981' : '#d1d5db',
                        borderRadius: '12px',
                        cursor: 'pointer',
                        position: 'relative',
                        transition: 'background-color 0.2s'
                      }}
                    >
                      <div style={{
                        width: '20px',
                        height: '20px',
                        backgroundColor: '#fff',
                        borderRadius: '50%',
                        position: 'absolute',
                        top: '2px',
                        left: stock.enabled ? '22px' : '2px',
                        transition: 'left 0.2s',
                        boxShadow: '0 1px 3px rgba(0,0,0,0.3)'
                      }}></div>
                    </div>
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
                  <td>{stock.max_amount?.toLocaleString()}원</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      <button
                        className="btn btn-secondary"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => handleEdit(stock)}
                      >
                        수정
                      </button>
                      <button
                        className="btn btn-danger"
                        style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                        onClick={() => handleDelete(stock.code)}
                      >
                        삭제
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <p style={{ color: 'var(--text-muted)' }}>등록된 종목이 없습니다.</p>
        )}
      </div>
    </div>
  );
}

export default Config;
