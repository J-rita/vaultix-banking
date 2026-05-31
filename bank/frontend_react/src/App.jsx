import React, { useState, useEffect } from 'react';

const App = () => {
  const [user, setUser] = useState(null);
  const [view, setView] = useState('login'); // login, dashboard, transfer
  const [accounts, setAccounts] = useState([]);
  const [token, setToken] = useState(localStorage.getItem('token'));

  useEffect(() => {
    if (token) {
      fetchAccounts();
    }
  }, [token]);

  const fetchAccounts = async () => {
    try {
      const res = await fetch('http://127.0.0.1:8000/api/accounts/my-accounts', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await res.json();
      setAccounts(data);
      setView('dashboard');
    } catch (err) {
      console.error(err);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const body = Object.fromEntries(formData);
    
    const res = await fetch('http://127.0.0.1:8000/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    });
    
    if (res.ok) {
      const data = await res.json();
      localStorage.setItem('token', data.access_token);
      setToken(data.access_token);
    } else {
      alert('Login Failed');
    }
  };

  const handleTransfer = async (e) => {
    e.preventDefault();
    const formData = new FormData(e.target);
    const body = Object.fromEntries(formData);
    body.amount = parseFloat(body.amount);

    const res = await fetch('http://127.0.0.1:8000/api/transactions/transfer', {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify(body)
    });

    if (res.ok) {
      alert('Transfer Successful!');
      fetchAccounts();
      setView('dashboard');
    } else {
      const err = await res.json();
      alert(err.detail || 'Transfer Failed');
    }
  };

  const renderLogin = () => (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
      <div className="glass-card" style={{ width: '400px' }}>
        <h2 style={{ textAlign: 'center', marginBottom: '2rem', color: 'var(--primary)' }}>KAY BANK Premium</h2>
        <form onSubmit={handleLogin}>
          <input name="username" placeholder="Username" className="input-field" required />
          <input name="password" type="password" placeholder="Password" className="input-field" required />
          <button type="submit" className="btn-primary" style={{ width: '100%' }}>Secure Sign In</button>
        </form>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div style={{ padding: '2rem' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '3rem' }}>
        <div>
          <h1 style={{ margin: 0 }}>Dashboard</h1>
          <p style={{ color: 'var(--text-muted)' }}>Manage your accounts and assets</p>
        </div>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button className="btn-primary" style={{ background: 'var(--bg-card)', border: '1px solid var(--primary)' }} onClick={() => { localStorage.clear(); window.location.reload(); }}>Logout</button>
          <button className="btn-primary" onClick={() => setView('transfer')}>New Transfer</button>
        </div>
      </header>

      <div className="dashboard-grid">
        {accounts.map(acc => (
          <div key={acc.ACCOUNT_ID} className="glass-card" style={{ borderLeft: `4px solid ${acc.ACCOUNT_TYPE === 'Savings' ? '#22c55e' : '#6366f1'}` }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
               <p style={{ color: 'var(--text-muted)', fontSize: '0.75rem', fontWeight: 'bold', textTransform: 'uppercase' }}>{acc.ACCOUNT_TYPE}</p>
               <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '12px', background: 'rgba(34, 197, 94, 0.2)', color: '#22c55e' }}>{acc.STATUS}</span>
            </div>
            <h3 style={{ margin: '0.5rem 0' }}>{acc.ACCOUNT_NUMBER}</h3>
            <h2 style={{ color: 'var(--text-main)', fontSize: '2rem' }}>₦{acc.BALANCE.toLocaleString()}</h2>
          </div>
        ))}
      </div>
    </div>
  );

  const renderTransfer = () => (
    <div style={{ padding: '2rem' }}>
      <button onClick={() => setView('dashboard')} style={{ background: 'none', color: 'var(--text-muted)', border: 'none', cursor: 'pointer', marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        ← Back to Dashboard
      </button>
      <div className="glass-card" style={{ maxWidth: '500px', margin: '0 auto' }}>
        <h2 style={{ marginBottom: '2rem' }}>Local Transfer</h2>
        <form onSubmit={handleTransfer}>
          <label style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>From Account</label>
          <select name="sender_id" className="input-field" required>
            {accounts.map(acc => (
              <option key={acc.ACCOUNT_ID} value={acc.ACCOUNT_ID}>{acc.ACCOUNT_NUMBER} (₦{acc.BALANCE.toLocaleString()})</option>
            ))}
          </select>

          <label style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Recipient Account Number</label>
          <input name="receiver_acc_num" placeholder="e.g. SAV-1234..." className="input-field" required />

          <label style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Amount (₦)</label>
          <input name="amount" type="number" step="0.01" placeholder="0.00" className="input-field" required />

          <label style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>Description (Optional)</label>
          <input name="description" placeholder="What's this for?" className="input-field" />

          <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '1rem' }}>Confirm Transfer</button>
        </form>
      </div>
    </div>
  );

  return (
    <div className="app-container" style={{ minHeight: '100vh' }}>
      {view === 'login' && renderLogin()}
      {view === 'dashboard' && renderDashboard()}
      {view === 'transfer' && renderTransfer()}
    </div>
  );
};

export default App;
