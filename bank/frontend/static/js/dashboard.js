/**
 * Vaultix Mobile Dashboard Logic
 * Handles balance, account info, greeting, and balance privacy toggle.
 */

const token = localStorage.getItem('token');
if (!token) window.location.href = '/login.html';

// ── Balance Privacy Toggle ───────────────────────────────────────────────────
let balanceHidden = true;
let currentBalance = null;

function toggleBalance() {
    balanceHidden = !balanceHidden;

    const eyeOpen   = document.getElementById('eyeOpen');
    const eyeClosed = document.getElementById('eyeClosed');
    const balEl     = document.getElementById('balanceValue');

    if (eyeOpen)   eyeOpen.style.display   = balanceHidden ? 'none'         : 'inline-block';
    if (eyeClosed) eyeClosed.style.display = balanceHidden ? 'inline-block' : 'none';

    if (balEl) {
        if (balanceHidden) {
            balEl.textContent = '••••••';
        } else {
            balEl.textContent = currentBalance !== null ? currentBalance : 'Loading...';
        }
    }
}

// ── Greeting ─────────────────────────────────────────────────────────────────
function setGreeting() {
    const hour = new Date().getHours();
    let greeting = 'Good Morning';
    if (hour >= 12 && hour < 17) greeting = 'Good Afternoon';
    else if (hour >= 17)         greeting = 'Good Evening';

    const el = document.getElementById('greeting');
    if (el) {
        const currentText = el.textContent;
        const namePart = currentText.includes(',') ? currentText.split(',')[1].trim() : 'User';
        el.textContent = greeting + ', ' + namePart;
    }
}

// ── Load Account Summary (balance + name) ─────────────────────────────────────
async function loadSummary() {
    try {
        const res = await fetch('/api/accounts/summary', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.status === 401) {
            localStorage.clear();
            window.location.href = '/login.html';
            return;
        }
        const data = await res.json();
        if (data.status === 'success') {
            currentBalance = '₦' + Number(data.total_balance).toLocaleString(undefined, {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });

            // Balance card — only show real value if user has already toggled open
            const balEl = document.getElementById('balanceValue');
            if (balEl && !balanceHidden) balEl.textContent = currentBalance;

            // Greeting name & Username
            const greetingEl = document.getElementById('greeting');
            const userNameEl = document.getElementById('userName');
            
            if (data.user_name) {
                const firstName = data.user_name.split(' ')[0];
                if (userNameEl) userNameEl.textContent = data.user_name;
                if (greetingEl) {
                    const currentText = greetingEl.textContent;
                    const greetingPart = currentText.includes(',') ? currentText.split(',')[0] : 'Good Morning';
                    greetingEl.textContent = greetingPart + ', ' + firstName;
                }
            }

            // Avatar initials
            const initEl = document.getElementById('userInitials');
            if (initEl && data.user_name) {
                const parts = data.user_name.split(' ');
                initEl.textContent = (parts[0][0] + (parts[1] ? parts[1][0] : '')).toUpperCase();
            }
        }
    } catch (err) {
        console.error('loadSummary error:', err);
    }
}

// ── Load Primary Account Number ───────────────────────────────────────────────
async function loadAccounts() {
    try {
        const res = await fetch('/api/accounts/my-accounts', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();
        if (data.status === 'success' && data.accounts.length > 0) {
            const accEl = document.getElementById('primaryAccNum');
            if (accEl) accEl.textContent = data.accounts[0].ACCOUNT_NUMBER;
        }
    } catch (err) {
        console.error('loadAccounts error:', err);
    }
}

// ── Load Recent Transactions ──────────────────────────────────────────────────
async function loadMobileTransactions() {
    const txList = document.getElementById('txList');
    if (!txList) return;

    try {
        const res = await fetch('/api/transactions/history', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const data = await res.json();

        if (data.status === 'success') {
            const recent = data.transactions.slice(0, 3);
            if (recent.length === 0) {
                txList.innerHTML = '<div style="text-align:center; padding:2rem; color:var(--text-muted);">No transactions yet</div>';
                return;
            }

            txList.innerHTML = recent.map(tx => {
                const isCredit = tx.TRANSACTION_TYPE === 'Deposit' ||
                                 tx.TRANSACTION_TYPE === 'Transfer_In' ||
                                 tx.TRANSACTION_TYPE.includes('Loan');
                const color  = isCredit ? 'var(--secondary)' : 'var(--text-dark)';
                const sign   = isCredit ? '+' : '-';
                const date   = new Date(tx.CREATED_AT).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
                const icon   = isCredit
                    ? `<svg width="20" height="20" stroke="var(--secondary)" fill="none" stroke-width="2"><path d="M12 19V5M5 12l7-7 7 7"/></svg>`
                    : `<svg width="20" height="20" stroke="var(--text-dark)" fill="none" stroke-width="2"><path d="M12 5v14M19 12l-7 7-7-7"/></svg>`;

                return `
                    <div class="tx-item">
                        <div style="display:flex; align-items:center;">
                            <div class="tx-icon">${icon}</div>
                            <div>
                                <div style="font-weight:600; font-size:0.95rem;">${tx.TRANSACTION_TYPE}</div>
                                <div style="font-size:0.75rem; color:var(--text-muted);">${date}</div>
                            </div>
                        </div>
                        <div style="font-weight:700; color:${color};">${sign}₦${tx.AMOUNT.toLocaleString()}</div>
                    </div>`;
            }).join('');
        }
    } catch (err) {
        console.error('loadMobileTransactions error:', err);
    }
}

// ── Logout ────────────────────────────────────────────────────────────────────
function logout() {
    localStorage.clear();
    window.location.href = '/login.html';
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    setGreeting();
    loadSummary();
    loadAccounts();
    loadMobileTransactions();
});

// ── Bill Payment Logic ────────────────────────────────────────────────────────
let selectedProvider = null;
let currentBillType = '';

function openBill(title, providers) {
    currentBillType = title;
    selectedProvider = null;
    document.getElementById('billTitle').textContent = title;
    document.getElementById('billNumber').value = '';
    document.getElementById('billAmount').value = '';

    const amountGroup = document.getElementById('amountGroup');
    const dataPlanGroup = document.getElementById('dataPlanGroup');

    if (title === 'Data Bundle') {
        amountGroup.style.display = 'none';
        dataPlanGroup.style.display = 'block';
    } else {
        amountGroup.style.display = 'block';
        dataPlanGroup.style.display = 'none';
    }

    const grid = document.getElementById('providerList');
    grid.innerHTML = providers.map(p =>
        `<div class="provider-pill" onclick="selectProvider(this, '${p}')">${p}</div>`
    ).join('');

    const modal = document.getElementById('billModal');
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);
}

function closeBill(e) {
    if (e && e.target && e.currentTarget && e.target !== e.currentTarget) return;
    const m = document.getElementById('billModal');
    m.classList.remove('active');
    setTimeout(() => m.style.display = 'none', 300);
}

function selectProvider(el, name) {
    document.querySelectorAll('.provider-pill').forEach(p => p.classList.remove('selected'));
    el.classList.add('selected');
    selectedProvider = name;
}

async function payBill() {
    if (!selectedProvider) { alert('Select a provider'); return; }
    const number = document.getElementById('billNumber').value.trim();
    
    let amount;
    let descriptionExt = '';
    if (currentBillType === 'Data Bundle') {
        const dp = document.getElementById('dataPlan');
        amount = parseFloat(dp.value);
        descriptionExt = ' - ' + dp.options[dp.selectedIndex].text.split(' - ')[0]; // Add the plan name (e.g. 1.5GB (30 Days))
    } else {
        amount = parseFloat(document.getElementById('billAmount').value);
    }

    if (!number) { alert('Enter a number'); return; }
    
    if (['Airtime Top-up', 'Data Bundle'].includes(currentBillType)) {
        if (number.length !== 11 || !/^\d+$/.test(number)) {
            alert('Phone number must be exactly 11 digits');
            return;
        }
    }

    if (!amount || amount < 50) { alert('Min ₦50'); return; }

    const btn = document.getElementById('payBtn');
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
        const accRes = await fetch('/api/accounts/my-accounts', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const accData = await accRes.json();
        if (!accData.accounts || accData.accounts.length === 0) {
            alert('No account found');
            return;
        }
        const accId = accData.accounts[0].ACCOUNT_ID;

        const res = await fetch('/api/transactions/withdraw', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({
                account_id: accId,
                amount: amount,
                description: `${currentBillType} - ${selectedProvider}${descriptionExt} - ${number}`
            })
        });
        const data = await res.json();

        if (data.status === 'success') {
            alert(`${currentBillType} payment of ₦${amount.toLocaleString()} to ${selectedProvider} was successful!`);
            closeBill(true);
            loadSummary(); // Refresh balance
            loadMobileTransactions(); // Refresh history
        } else {
            alert('Payment failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (err) {
        alert('Network error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Pay Now';
    }
}

// ── Add Money Logic ───────────────────────────────────────────────────────────
function openAddMoney() {
    const modal = document.getElementById('addMoneyModal');
    if (!modal) return;
    document.getElementById('depositAmount').value = '';
    modal.style.display = 'flex';
    setTimeout(() => modal.classList.add('active'), 10);
}

function closeAddMoney(e) {
    if (e && e.target && e.currentTarget && e.target !== e.currentTarget) return;
    const m = document.getElementById('addMoneyModal');
    if (!m) return;
    m.classList.remove('active');
    setTimeout(() => m.style.display = 'none', 300);
}

async function submitAddMoney() {
    const amountStr = document.getElementById('depositAmount').value;
    const amount = parseFloat(amountStr);
    
    if (!amount || amount < 100) {
        alert('Please enter a valid amount (Minimum ₦100)');
        return;
    }

    const btn = document.getElementById('depositBtn');
    btn.disabled = true;
    btn.textContent = 'Processing...';

    try {
        const accRes = await fetch('/api/accounts/my-accounts', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        const accData = await accRes.json();
        if (!accData.accounts || accData.accounts.length === 0) {
            alert('No active account found to fund.');
            return;
        }
        const accId = accData.accounts[0].ACCOUNT_ID;

        const res = await fetch('/api/transactions/deposit', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
            body: JSON.stringify({
                account_id: accId,
                amount: amount
            })
        });
        const data = await res.json();

        if (data.status === 'success') {
            alert(`Successfully deposited ₦${amount.toLocaleString()} into your account!`);
            closeAddMoney(true);
            loadSummary(); // Refresh balance
            loadMobileTransactions(); // Refresh history
        } else {
            alert('Deposit failed: ' + (data.detail || 'Unknown error'));
        }
    } catch (err) {
        alert('Network error while processing deposit.');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Fund Account';
    }
}

