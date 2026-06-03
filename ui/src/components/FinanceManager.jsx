import { useState, useEffect, useCallback } from "react";
import api from "../api";
import "./FinanceManager.css";

const CATEGORY_COLORS = {
  food: "#fbbf24", transport: "#60a5fa", shopping: "#f472b6",
  entertainment: "#a78bfa", utilities: "#34d399", health: "#f87171",
  finance: "#2dd4bf", travel: "#fb923c", uncategorized: "#94a3b8",
};

const SEVERITY_ICON = { critical: "🔴", high: "🟠", normal: "🟡", low: "🟢" };

function formatCurrency(val, currency = "USD") {
  if (val == null) return "—";
  const symbol = currency === "INR" ? "₹" : currency === "EUR" ? "€" : currency === "GBP" ? "£" : "$";
  return `${symbol}${Number(val).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function formatCrypto(val) {
  if (val == null) return "—";
  return Number(val).toLocaleString(undefined, { minimumFractionDigits: 4, maximumFractionDigits: 6 });
}

function StatCard({ label, value, sub, color = "#34d399" }) {
  return (
    <div className="fm-stat-card">
      <span className="fm-stat-label">{label}</span>
      <span className="fm-stat-value" style={{ color }}>{value}</span>
      {sub && <span className="fm-stat-sub">{sub}</span>}
    </div>
  );
}

function CategoryBar({ category, amount, total, budget }) {
  const pct = total > 0 ? (amount / total) * 100 : 0;
  const budgetPct = budget > 0 ? (amount / budget) * 100 : 0;
  const color = CATEGORY_COLORS[category] || CATEGORY_COLORS.uncategorized;
  const overBudget = budget > 0 && amount > budget;
  return (
    <div className="fm-cat-bar">
      <div className="fm-cat-header">
        <span className="fm-cat-name" style={{ color }}>{category}</span>
        <span className="fm-cat-amount">{formatCurrency(amount)}</span>
      </div>
      <div className="fm-cat-track">
        <div className="fm-cat-fill" style={{ width: `${Math.min(100, pct)}%`, background: color }} />
        {budget > 0 && <div className="fm-cat-budget-line" style={{ left: `${Math.min(100, budgetPct)}%` }} />}
      </div>
      <div className="fm-cat-meta">
        <span>{pct.toFixed(1)}% of spend</span>
        {budget > 0 && <span className={overBudget ? "fm-over-budget" : ""}>Budget: {formatCurrency(budget)} {overBudget && "(over!)"}</span>}
      </div>
    </div>
  );
}

export default function FinanceManager() {
  const [activeTab, setActiveTab] = useState("overview");
  const [stats, setStats] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filterCategory, setFilterCategory] = useState("");

  // Trading state
  const [portfolio, setPortfolio] = useState(null);
  const [marketPrice, setMarketPrice] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);

  // Trade form
  const [tradeSymbol, setTradeSymbol] = useState("BTC-USDT");
  const [tradeSide, setTradeSide] = useState("BUY");
  const [tradeQty, setTradeQty] = useState("");
  const [tradePaper, setTradePaper] = useState(true);
  const [tradeResult, setTradeResult] = useState(null);

  // ATE live signals
  const [liveSignal, setLiveSignal] = useState(null);
  const [autoTradeEnabled, setAutoTradeEnabled] = useState(() => localStorage.getItem("love_auto_paper_trade") === "true");

  // Noise / dismiss
  const [showDismissed, setShowDismissed] = useState(false);
  const [editingTx, setEditingTx] = useState(null);

  // Backtest form
  const [btStrategy, setBtStrategy] = useState("sma_crossover");
  const [btSymbol, setBtSymbol] = useState("BTC-USDT");
  const [btInterval, setBtInterval] = useState("1h");
  const [btLimit, setBtLimit] = useState("500");
  const [btBalance, setBtBalance] = useState("10000");
  const [btParams, setBtParams] = useState({});

  // Add transaction form
  const [formAmount, setFormAmount] = useState("");
  const [formMerchant, setFormMerchant] = useState("");
  const [formCategory, setFormCategory] = useState("uncategorized");
  const [formCurrency, setFormCurrency] = useState("USD");

  // Budget form
  const [budgetCat, setBudgetCat] = useState("");
  const [budgetLimit, setBudgetLimit] = useState("");

  // Parse text
  const [parseText, setParseText] = useState("");
  const [parseResult, setParseResult] = useState(null);

  // Autonomous trading state
  const [genStrategies, setGenStrategies] = useState([]);
  const [ateStatus, setAteStatus] = useState(null);
  const [evolutionLog, setEvolutionLog] = useState([]);
  const [autoTrades, setAutoTrades] = useState([]);
  const [genLoading, setGenLoading] = useState(false);

  // Learned patterns state
  const [learnedProfile, setLearnedProfile] = useState(null);
  const [learnedMood, setLearnedMood] = useState(null);
  const [learnedMerchants, setLearnedMerchants] = useState([]);
  const [learnedRecurring, setLearnedRecurring] = useState([]);
  const [learnedAnomalies, setLearnedAnomalies] = useState([]);
  const [learnedSuggestions, setLearnedSuggestions] = useState([]);

  // Quantitative module state
  const [quantSignals, setQuantSignals] = useState(null);
  const [quantRegime, setQuantRegime] = useState(null);
  const [quantSentiment, setQuantSentiment] = useState(null);
  const [quantRisk, setQuantRisk] = useState(null);
  const [quantPortfolio, setQuantPortfolio] = useState(null);
  const [quantSymbol, setQuantSymbol] = useState("BTC-USDT");
  const [quantLoading, setQuantLoading] = useState(false);

  const categories = Object.keys(CATEGORY_COLORS);

  const fetchAll = useCallback(async () => {
    setLoading(true);
    try {
      const [sRes, tRes, aRes, pRes, priceRes, stratRes, genRes, ateRes, evoRes, autoRes, sigRes,
             profRes, moodRes, merchRes, recRes, anomRes, suggRes,
             qSigRes, qRegRes, qSenRes, qRiskRes] = await Promise.allSettled([
        api.get("/finance/stats"),
        api.get(`/finance/transactions?limit=50&include_dismissed=${showDismissed}${filterCategory ? `&category=${filterCategory}` : ""}`),
        api.get("/finance/alerts?limit=20"),
        api.get("/finance/portfolio"),
        api.get("/finance/price?symbol=BTC-USDT"),
        api.get("/finance/strategies"),
        api.get("/finance/autonomous/strategies"),
        api.get("/finance/autonomous/status"),
        api.get("/finance/autonomous/evolution-log"),
        api.get("/finance/autonomous/auto-trades"),
        api.get("/finance/autonomous/signals"),
        api.get("/learning/profile"),
        api.get("/learning/mood"),
        api.get("/learning/merchants"),
        api.get("/learning/recurring"),
        api.get("/learning/anomalies"),
        api.get("/learning/suggestions"),
        api.get(`/finance/quant/signals?symbol=${quantSymbol}`),
        api.get(`/finance/quant/regime?symbol=${quantSymbol}`),
        api.get(`/finance/quant/sentiment?symbol=${quantSymbol}`),
        api.get("/finance/quant/risk"),
      ]);
      if (sRes.status === "fulfilled") setStats(sRes.value.data);
      if (tRes.status === "fulfilled") setTransactions(tRes.value.data.transactions || []);
      if (aRes.status === "fulfilled") setAlerts(aRes.value.data.alerts || []);
      if (pRes.status === "fulfilled") setPortfolio(pRes.value.data);
      if (priceRes.status === "fulfilled") {
        const d = priceRes.value.data;
        setMarketPrice(d?.price || d?.lastPrice || null);
      }
      if (stratRes.status === "fulfilled") setStrategies(stratRes.value.data.strategies || []);
      if (genRes.status === "fulfilled") setGenStrategies(genRes.value.data.strategies || []);
      if (ateRes.status === "fulfilled") setAteStatus(ateRes.value.data);
      if (evoRes.status === "fulfilled") setEvolutionLog(evoRes.value.data.entries || []);
      if (autoRes.status === "fulfilled") setAutoTrades(autoRes.value.data.trades || []);
      if (sigRes.status === "fulfilled") setLiveSignal(sigRes.value.data);
      if (profRes.status === "fulfilled") setLearnedProfile(profRes.value.data.profile || null);
      if (moodRes.status === "fulfilled") setLearnedMood(moodRes.value.data);
      if (merchRes.status === "fulfilled") setLearnedMerchants(merchRes.value.data.merchants || []);
      if (recRes.status === "fulfilled") setLearnedRecurring(recRes.value.data.recurring || []);
      if (anomRes.status === "fulfilled") setLearnedAnomalies(anomRes.value.data.anomalies || []);
      if (suggRes.status === "fulfilled") setLearnedSuggestions(suggRes.value.data.suggestions || []);
      if (qSigRes.status === "fulfilled") setQuantSignals(qSigRes.value.data);
      if (qRegRes.status === "fulfilled") setQuantRegime(qRegRes.value.data);
      if (qSenRes.status === "fulfilled") setQuantSentiment(qSenRes.value.data);
      if (qRiskRes.status === "fulfilled") setQuantRisk(qRiskRes.value.data);
    } catch (e) {
      console.error("[FinanceManager] fetch error:", e);
    } finally {
      setLoading(false);
    }
  }, [filterCategory, showDismissed, quantSymbol]);

  useEffect(() => {
    fetchAll();
    const id = setInterval(fetchAll, 10000);
    return () => clearInterval(id);
  }, [fetchAll]);

  useEffect(() => {
    localStorage.setItem("love_auto_paper_trade", autoTradeEnabled ? "true" : "false");
  }, [autoTradeEnabled]);

  const addTransaction = async () => {
    if (!formAmount || !formMerchant) return;
    try {
      await api.post("/finance/transaction", {
        amount: parseFloat(formAmount), merchant: formMerchant,
        category: formCategory, currency: formCurrency,
      });
      setFormAmount(""); setFormMerchant(""); setFormCategory("uncategorized");
      fetchAll();
    } catch (e) {
      alert("Failed to add: " + (e.response?.data?.error || e.message));
    }
  };

  const setBudget = async () => {
    if (!budgetCat || !budgetLimit) return;
    try {
      await api.post("/finance/budget", { category: budgetCat, limit: parseFloat(budgetLimit) });
      setBudgetCat(""); setBudgetLimit(""); fetchAll();
    } catch (e) {
      alert("Failed: " + (e.response?.data?.error || e.message));
    }
  };

  const parseNotification = async () => {
    if (!parseText.trim()) return;
    try {
      const res = await api.post("/finance/parse", { text: parseText });
      setParseResult(res.data);
      if (res.data.success) { setParseText(""); fetchAll(); }
    } catch (e) {
      setParseResult({ success: false, error: e.response?.data?.error || e.message });
    }
  };

  const placeTrade = async () => {
    if (!tradeQty) return;
    try {
      const res = await api.post("/finance/trade", {
        symbol: tradeSymbol, side: tradeSide, quantity: parseFloat(tradeQty),
        paper: tradePaper,
      });
      setTradeResult(res.data);
      if (res.data.success) { setTradeQty(""); fetchAll(); }
    } catch (e) {
      setTradeResult({ success: false, error: e.response?.data?.error || e.message });
    }
  };

  const runBacktest = async () => {
    setBacktestLoading(true);
    setBacktestResult(null);
    try {
      const res = await api.post("/finance/backtest", {
        strategy: btStrategy, symbol: btSymbol, interval: btInterval,
        limit: parseInt(btLimit), initial_balance: parseFloat(btBalance),
        params: Object.keys(btParams).length > 0 ? btParams : undefined,
      });
      setBacktestResult(res.data);
    } catch (e) {
      setBacktestResult({ error: e.response?.data?.error || e.message });
    } finally {
      setBacktestLoading(false);
    }
  };

  const forceGenerateStrategy = async () => {
    setGenLoading(true);
    try {
      await api.post("/finance/autonomous/generate");
      fetchAll();
    } catch (e) {
      console.error("[FinanceManager] force generate error:", e);
    } finally {
      setGenLoading(false);
    }
  };

  const forceAutoPaperTrade = async () => {
    try {
      await api.post("/finance/autonomous/paper-trade");
      fetchAll();
    } catch (e) {
      console.error("[FinanceManager] force paper trade error:", e);
    }
  };

  const toggleAutoTrade = async (enabled) => {
    try {
      await api.post("/finance/autonomous/toggle-auto", { enabled });
      setAutoTradeEnabled(enabled);
    } catch (e) {
      console.error("[FinanceManager] toggle auto trade error:", e);
    }
  };

  const dismissTx = async (txId) => {
    try {
      await api.post(`/finance/transactions/${encodeURIComponent(txId)}/dismiss`);
      fetchAll();
    } catch (e) {
      console.error("[FinanceManager] dismiss error:", e);
    }
  };

  const recategorizeTx = async (txId, newCat) => {
    try {
      await api.post(`/finance/transactions/${encodeURIComponent(txId)}/recategorize`, { category: newCat });
      setEditingTx(null);
      fetchAll();
    } catch (e) {
      console.error("[FinanceManager] recategorize error:", e);
    }
  };

  const totalSpent7d = stats?.total_spent_7d || 0;
  const totalSpent30d = stats?.total_spent_30d || 0;
  const suspiciousCount = stats?.suspicious_count || 0;
  const categorySpending = stats?.category_spending_7d || {};
  const activeBudgets = stats?.active_budgets || {};
  const paperPortfolio = portfolio?.paper || {};
  const paperPositions = paperPortfolio.positions || [];

  return (
    <div className="finance-manager">
      <div className="fm-header">
        <div className="fm-title">
          <span className="fm-icon">💰</span>
          <h2>Finance Guardian</h2>
          <span className="fm-subtitle">
            {stats ? `${stats.transactions_7d} txs · ${stats.monitored_merchants} merchants` : "Loading…"}
          </span>
          {portfolio && (
            <span className={`fm-mode-badge ${portfolio.mode}`}>
              {portfolio.mode === "paper" ? "🧪 Paper" : "🔴 Live"}
            </span>
          )}
        </div>
        {loading && <span className="fm-loading">⟳</span>}
      </div>

      <div className="fm-stats-row">
        <StatCard label="7-Day Spend" value={formatCurrency(totalSpent7d)} sub={`${stats?.transactions_7d || 0} txs`} color="#fbbf24" />
        <StatCard label="30-Day Spend" value={formatCurrency(totalSpent30d)} sub={`${stats?.transactions_30d || 0} txs`} color="#60a5fa" />
        <StatCard label="Suspicious Alerts" value={suspiciousCount} sub={suspiciousCount > 0 ? "Review immediately" : "All clear"} color={suspiciousCount > 0 ? "#f87171" : "#34d399"} />
        <StatCard label="Paper Equity" value={formatCurrency(paperPortfolio.total_equity, "USDT")} sub={`${paperPositions.length} positions`} color="#a78bfa" />
      </div>

      <nav className="fm-tabs">
        {["overview", "transactions", "alerts", "budgets", "trading", "quant", "autonomous", "learned", "add", "parse"].map(tab => (
          <button key={tab} className={`fm-tab ${activeTab === tab ? "active" : ""}`} onClick={() => setActiveTab(tab)}>
            {tab === "overview" && "Overview"}
            {tab === "transactions" && "Transactions"}
            {tab === "alerts" && "Alerts"}
            {tab === "budgets" && "Budgets"}
            {tab === "trading" && "📈 Trading"}
            {tab === "quant" && "🔬 Quant"}
            {tab === "autonomous" && "🧠 Auto"}
            {tab === "learned" && "🔮 Learned"}
            {tab === "add" && "+ Add"}
            {tab === "parse" && "Parse SMS"}
          </button>
        ))}
      </nav>

      <div className="fm-content">
        {/* ── OVERVIEW ── */}
        {activeTab === "overview" && (
          <div className="fm-overview">
            <div className="fm-section">
              <h4>Spending by Category (7 days)</h4>
              {Object.keys(categorySpending).length === 0 ? (
                <p className="fm-empty">No category data yet. Add transactions or let LOVE parse your bank notifications.</p>
              ) : (
                <div className="fm-cat-list">
                  {Object.entries(categorySpending).sort((a, b) => b[1] - a[1]).map(([cat, amt]) => (
                    <CategoryBar key={cat} category={cat} amount={amt} total={totalSpent7d} budget={activeBudgets[cat]} />
                  ))}
                </div>
              )}
            </div>
            {alerts.length > 0 && (
              <div className="fm-section">
                <h4>Recent Alerts</h4>
                <div className="fm-alert-list">
                  {alerts.slice(0, 5).map((alert, i) => (
                    <div key={i} className={`fm-alert-card severity-${alert.severity}`}>
                      <span className="fm-alert-icon">{SEVERITY_ICON[alert.severity] || "⚪"}</span>
                      <span className="fm-alert-msg">{alert.message}</span>
                      <span className="fm-alert-time">{alert.timestamp ? new Date(alert.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            {transactions.length > 0 && (
              <div className="fm-section">
                <h4>Latest Transactions</h4>
                <div className="fm-tx-mini">
                  {transactions.slice(0, 5).map((tx, i) => (
                    <div key={i} className="fm-tx-row">
                      <span className="fm-tx-merchant">{tx.merchant}</span>
                      <span className="fm-tx-cat" style={{ color: CATEGORY_COLORS[tx.category] || CATEGORY_COLORS.uncategorized }}>{tx.category}</span>
                      <span className="fm-tx-amt">{formatCurrency(tx.amount, tx.currency)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── TRANSACTIONS ── */}
        {activeTab === "transactions" && (
          <div className="fm-transactions">
            <div className="fm-filter-bar">
              <select value={filterCategory} onChange={e => setFilterCategory(e.target.value)} className="fm-select">
                <option value="">All categories</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <label className="fm-toggle">
                <input type="checkbox" checked={showDismissed} onChange={e => setShowDismissed(e.target.checked)} />
                <span>Show dismissed</span>
              </label>
              <span className="fm-tx-count">{transactions.length} transactions</span>
            </div>
            {transactions.length === 0 ? (
              <p className="fm-empty">No transactions yet. Use the Add or Parse tabs.</p>
            ) : (
              <div className="fm-tx-table">
                <div className="fm-tx-header">
                  <span>Time</span><span>Merchant</span><span>Category</span><span>Source</span><span style={{ textAlign: "right" }}>Amount</span><span>Actions</span>
                </div>
                {transactions.map((tx, i) => (
                  <div key={i} className={`fm-tx-row ${tx.dismissed ? "fm-tx-dismissed" : ""}`}>
                    <span className="fm-tx-time">{tx.timestamp ? new Date(tx.timestamp).toLocaleDateString([], { month: "short", day: "numeric" }) + " " + new Date(tx.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "—"}</span>
                    <span className="fm-tx-merchant" title={tx.raw_text}>{tx.merchant}</span>
                    <span className="fm-tx-cat" style={{ color: CATEGORY_COLORS[tx.category] || CATEGORY_COLORS.uncategorized }}>
                      {editingTx === tx.id ? (
                        <select value={tx.category} onChange={e => recategorizeTx(tx.id, e.target.value)} onBlur={() => setEditingTx(null)} autoFocus>
                          {categories.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                      ) : (
                        tx.category
                      )}
                    </span>
                    <span className="fm-tx-source">{tx.source}</span>
                    <span className="fm-tx-amt">{formatCurrency(tx.amount, tx.currency)}</span>
                    <span className="fm-tx-actions">
                      {!tx.dismissed && (
                        <>
                          <button className="fm-action-btn" title="Recategorize" onClick={() => setEditingTx(tx.id)}>🏷️</button>
                          <button className="fm-action-btn" title="Dismiss as noise" onClick={() => dismissTx(tx.id)}>🗑️</button>
                        </>
                      )}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── ALERTS ── */}
        {activeTab === "alerts" && (
          <div className="fm-alerts">
            {alerts.length === 0 ? (
              <p className="fm-empty">No alerts. All financial activity looks normal.</p>
            ) : (
              <div className="fm-alert-full">
                {alerts.map((alert, i) => (
                  <div key={i} className={`fm-alert-card severity-${alert.severity}`}>
                    <div className="fm-alert-header">
                      <span className="fm-alert-icon">{SEVERITY_ICON[alert.severity] || "⚪"}</span>
                      <span className="fm-alert-type">{alert.type?.replace(/_/g, " ")}</span>
                      <span className="fm-alert-time">{alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ""}</span>
                    </div>
                    <div className="fm-alert-msg">{alert.message}</div>
                    {alert.z_score != null && <div className="fm-alert-meta">Z-score: {alert.z_score}</div>}
                    {alert.spent != null && alert.limit != null && (
                      <div className="fm-alert-meta">Spent: {formatCurrency(alert.spent)} / Limit: {formatCurrency(alert.limit)}</div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── BUDGETS ── */}
        {activeTab === "budgets" && (
          <div className="fm-budgets">
            <div className="fm-form-row">
              <input className="fm-input" placeholder="Category (e.g. food)" value={budgetCat} onChange={e => setBudgetCat(e.target.value)} list="cat-list" />
              <datalist id="cat-list">{categories.map(c => <option key={c} value={c} />)}</datalist>
              <input className="fm-input" type="number" placeholder="Monthly limit" value={budgetLimit} onChange={e => setBudgetLimit(e.target.value)} />
              <button className="fm-btn" onClick={setBudget}>Set Budget</button>
            </div>
            <div className="fm-budget-list">
              {Object.keys(activeBudgets).length === 0 ? (
                <p className="fm-empty">No budgets set. Use the form above to start tracking spending limits.</p>
              ) : (
                Object.entries(activeBudgets).map(([cat, limit]) => {
                  const spent = categorySpending[cat] || 0;
                  const pct = limit > 0 ? (spent / limit) * 100 : 0;
                  const over = spent > limit;
                  return (
                    <div key={cat} className={`fm-budget-card ${over ? "over" : ""}`}>
                      <div className="fm-budget-info">
                        <span className="fm-budget-cat" style={{ color: CATEGORY_COLORS[cat] || CATEGORY_COLORS.uncategorized }}>{cat}</span>
                        <span className="fm-budget-num">{formatCurrency(spent)} / {formatCurrency(limit)}</span>
                      </div>
                      <div className="fm-budget-track">
                        <div className="fm-budget-fill" style={{ width: `${Math.min(100, pct)}%`, background: over ? "#f87171" : pct > 80 ? "#fbbf24" : "#34d399" }} />
                      </div>
                      <div className="fm-budget-pct">{pct.toFixed(0)}%</div>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        )}

        {/* ── QUANT ── */}
        {activeTab === "quant" && (
          <div className="fm-quant">
            <div className="fm-section">
              <div className="fm-form-row">
                <input className="fm-input" placeholder="Symbol (e.g. BTC-USDT)" value={quantSymbol} onChange={e => setQuantSymbol(e.target.value)} />
                <button className="fm-btn" onClick={fetchAll} disabled={loading}>Refresh</button>
              </div>
            </div>

            {/* Signal Card */}
            {quantSignals && (
              <div className="fm-section">
                <h4>Ensemble Signal</h4>
                <div className={`fm-signal-card fm-signal-${(quantSignals.signal || "HOLD").toLowerCase()}`}>
                  <div className="fm-signal-main">
                    <span className="fm-signal-badge">{quantSignals.signal || "HOLD"}</span>
                    <span>Score: {(quantSignals.score || 0).toFixed(2)}</span>
                    <span>Confidence: {((quantSignals.confidence || 0) * 100).toFixed(0)}%</span>
                  </div>
                  {quantSignals.details && (
                    <div className="fm-signal-meta">
                      {Object.entries(quantSignals.details).map(([k, v]) => {
                        let display = "";
                        if (typeof v === "number") display = v.toFixed(2);
                        else if (v && typeof v === "object" && "signal" in v) display = `sig ${v.signal.toFixed(2)} / conf ${(v.confidence * 100).toFixed(0)}%`;
                        else display = String(v);
                        return <span key={k}>{k}: {display}</span>;
                      })}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Regime + Sentiment row */}
            <div className="fm-section">
              <div className="fm-portfolio-stats">
                {quantRegime && (
                  <StatCard label="Market Regime" value={quantRegime.regime || "UNKNOWN"} sub={`Confidence: ${((quantRegime.confidence || 0) * 100).toFixed(0)}%`} color="#60a5fa" />
                )}
                {quantSentiment && (
                  <StatCard
                    label="Sentiment"
                    value={quantSentiment.regime || "NEUTRAL"}
                    sub={`Score: ${(quantSentiment.sentiment || 0).toFixed(2)}`}
                    color={quantSentiment.sentiment > 0.3 ? "#34d399" : quantSentiment.sentiment < -0.3 ? "#f87171" : "#fbbf24"}
                  />
                )}
              </div>
            </div>

            {/* Risk Status */}
            {quantRisk && (
              <div className="fm-section">
                <h4>Risk Status</h4>
                <div className="fm-portfolio-stats">
                  <StatCard label="Capital" value={formatCurrency(quantRisk.current_capital || 0)} color="#34d399" />
                  <StatCard label="Drawdown" value={`${(quantRisk.drawdown_pct || 0).toFixed(2)}%`} sub={quantRisk.circuit_breaker ? "CIRCUIT BREAKER" : "OK"} color={quantRisk.circuit_breaker ? "#f87171" : "#34d399"} />
                  <StatCard label="VaR 95%" value={`${(quantRisk.var_95_pct || 0).toFixed(2)}%`} color="#60a5fa" />
                  <StatCard label="Kelly" value={`${((quantRisk.kelly_fraction || 0) * 100).toFixed(1)}%`} color="#a78bfa" />
                  <StatCard label="Win Rate" value={`${((quantRisk.win_rate || 0) * 100).toFixed(1)}%`} sub={`${quantRisk.total_trades || 0} trades`} color="#fbbf24" />
                </div>
              </div>
            )}

            {/* Portfolio Optimizer */}
            <div className="fm-section">
              <h4>Portfolio Optimizer</h4>
              <div className="fm-form-row">
                <button className="fm-btn" onClick={async () => {
                  setQuantLoading(true);
                  try {
                    const returns = {
                      BTC: [0.01, -0.005, 0.02, 0.01, -0.01, 0.015, 0.005, -0.008, 0.012, 0.003],
                      ETH: [0.008, -0.003, 0.015, 0.012, -0.008, 0.01, 0.003, -0.005, 0.009, 0.004],
                    };
                    const res = await api.post("/finance/quant/portfolio", { returns, method: "sharpe" });
                    setQuantPortfolio(res.data);
                  } catch (e) { console.error(e); }
                  finally { setQuantLoading(false); }
                }} disabled={quantLoading}>
                  {quantLoading ? "Optimizing…" : "Run Sharpe Optimizer"}
                </button>
              </div>
              {quantPortfolio && !quantPortfolio.error && (
                <div className="fm-backtest-stats">
                  <StatCard label="Method" value={quantPortfolio.method || "sharpe"} color="#60a5fa" />
                  <StatCard label="Sharpe" value={(quantPortfolio.sharpe || 0).toFixed(2)} color="#fbbf24" />
                  <StatCard label="Expected Return" value={`${((quantPortfolio.expected_return || 0) * 100).toFixed(2)}%`} color="#34d399" />
                  <StatCard label="Volatility" value={`${((quantPortfolio.volatility || 0) * 100).toFixed(2)}%`} color="#a78bfa" />
                </div>
              )}
              {quantPortfolio?.weights && (
                <div className="fm-cat-list" style={{ marginTop: 12 }}>
                  {Object.entries(quantPortfolio.weights).map(([sym, w]) => (
                    <CategoryBar key={sym} category={sym} amount={w} total={1} budget={0} />
                  ))}
                </div>
              )}
              {quantPortfolio?.error && (
                <div className="fm-parse-result error"><span>❌</span><span>{quantPortfolio.error}</span></div>
              )}
            </div>
          </div>
        )}

        {/* ── TRADING ── */}
        {activeTab === "trading" && (
          <div className="fm-trading">
            {/* Portfolio Summary */}
            <div className="fm-section">
              <h4>Paper Trading Portfolio</h4>
              <div className="fm-portfolio-stats">
                <StatCard label="Balance" value={formatCurrency(paperPortfolio.balance, "USDT")} color="#34d399" />
                <StatCard label="Position Value" value={formatCurrency(paperPortfolio.position_value, "USDT")} color="#60a5fa" />
                <StatCard label="Total Equity" value={formatCurrency(paperPortfolio.total_equity, "USDT")} color="#a78bfa" />
                <StatCard label="Positions" value={paperPortfolio.position_count || 0} color="#fbbf24" />
              </div>

              {paperPositions.length > 0 && (
                <div className="fm-positions">
                  <h5>Open Positions</h5>
                  <div className="fm-tx-table">
                    <div className="fm-tx-header">
                      <span>Symbol</span><span>Qty</span><span>Entry</span><span>Current</span><span>Unrealized</span><span>Value</span>
                    </div>
                    {paperPositions.map((pos, i) => (
                      <div key={i} className="fm-tx-row">
                        <span className="fm-tx-merchant">{pos.symbol}</span>
                        <span>{formatCrypto(pos.quantity)}</span>
                        <span>{formatCurrency(pos.avg_entry, "USDT")}</span>
                        <span>{formatCurrency(pos.current_price, "USDT")}</span>
                        <span style={{ color: pos.unrealized_pnl >= 0 ? "#34d399" : "#f87171" }}>
                          {pos.unrealized_pnl >= 0 ? "+" : ""}{formatCurrency(pos.unrealized_pnl, "USDT")} ({pos.unrealized_pct >= 0 ? "+" : ""}{pos.unrealized_pct.toFixed(2)}%)
                        </span>
                        <span>{formatCurrency(pos.value, "USDT")}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Order Entry */}
            <div className="fm-section">
              <h4>Place Order</h4>
              <div className="fm-form-row">
                <input className="fm-input" placeholder="Symbol (e.g. BTC-USDT)" value={tradeSymbol} onChange={e => setTradeSymbol(e.target.value)} />
                <select className="fm-select" value={tradeSide} onChange={e => setTradeSide(e.target.value)}>
                  <option value="BUY">BUY</option>
                  <option value="SELL">SELL</option>
                </select>
                <input className="fm-input" type="number" step="0.0001" placeholder="Quantity" value={tradeQty} onChange={e => setTradeQty(e.target.value)} />
                <label className="fm-toggle">
                  <input type="checkbox" checked={tradePaper} onChange={e => setTradePaper(e.target.checked)} />
                  <span>Paper Mode</span>
                </label>
                <button className="fm-btn fm-btn-primary" onClick={placeTrade}>Execute</button>
              </div>
              {marketPrice && (
                <div className="fm-price-tag">Current {tradeSymbol} price: <strong>{formatCurrency(marketPrice, "USDT")}</strong></div>
              )}
              {tradeResult && (
                <div className={`fm-parse-result ${tradeResult.success ? "success" : "error"}`}>
                  {tradeResult.success ? (
                    <>
                      <span className="fm-parse-icon">✅</span>
                      <span>Order filled: {tradeResult.order?.side} {formatCrypto(tradeResult.order?.quantity)} {tradeResult.order?.symbol} @ {formatCurrency(tradeResult.order?.price, "USDT")}</span>
                    </>
                  ) : (
                    <>
                      <span className="fm-parse-icon">❌</span>
                      <span>{tradeResult.error || "Trade failed"}</span>
                    </>
                  )}
                </div>
              )}
            </div>

            {/* Strategy Backtester */}
            <div className="fm-section">
              <h4>Strategy Backtester</h4>
              <div className="fm-form-row">
                <select className="fm-select" value={btStrategy} onChange={e => { setBtStrategy(e.target.value); setBtParams({}); }}>
                  {strategies.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                </select>
                <input className="fm-input" placeholder="Symbol" value={btSymbol} onChange={e => setBtSymbol(e.target.value)} />
                <select className="fm-select" value={btInterval} onChange={e => setBtInterval(e.target.value)}>
                  <option value="1h">1H</option>
                  <option value="4h">4H</option>
                  <option value="1d">1D</option>
                </select>
                <input className="fm-input" type="number" placeholder="Candles" value={btLimit} onChange={e => setBtLimit(e.target.value)} />
                <input className="fm-input" type="number" placeholder="Initial Balance" value={btBalance} onChange={e => setBtBalance(e.target.value)} />
                <button className="fm-btn fm-btn-primary" onClick={runBacktest} disabled={backtestLoading}>
                  {backtestLoading ? "Running…" : "Run Backtest"}
                </button>
              </div>

              {/* Strategy-specific params */}
              {btStrategy === "sma_crossover" && (
                <div className="fm-form-row">
                  <input className="fm-input" type="number" placeholder="Fast period" value={btParams.fast || ""} onChange={e => setBtParams(p => ({ ...p, fast: e.target.value }))} />
                  <input className="fm-input" type="number" placeholder="Slow period" value={btParams.slow || ""} onChange={e => setBtParams(p => ({ ...p, slow: e.target.value }))} />
                </div>
              )}
              {btStrategy === "rsi" && (
                <div className="fm-form-row">
                  <input className="fm-input" type="number" placeholder="Period" value={btParams.period || ""} onChange={e => setBtParams(p => ({ ...p, period: e.target.value }))} />
                  <input className="fm-input" type="number" placeholder="Oversold" value={btParams.oversold || ""} onChange={e => setBtParams(p => ({ ...p, oversold: e.target.value }))} />
                  <input className="fm-input" type="number" placeholder="Overbought" value={btParams.overbought || ""} onChange={e => setBtParams(p => ({ ...p, overbought: e.target.value }))} />
                </div>
              )}
              {btStrategy === "macd" && (
                <div className="fm-form-row">
                  <input className="fm-input" type="number" placeholder="Fast" value={btParams.fast || ""} onChange={e => setBtParams(p => ({ ...p, fast: e.target.value }))} />
                  <input className="fm-input" type="number" placeholder="Slow" value={btParams.slow || ""} onChange={e => setBtParams(p => ({ ...p, slow: e.target.value }))} />
                  <input className="fm-input" type="number" placeholder="Signal" value={btParams.signal || ""} onChange={e => setBtParams(p => ({ ...p, signal: e.target.value }))} />
                </div>
              )}

              {backtestResult && !backtestResult.error && (
                <div className="fm-backtest-result">
                  <div className="fm-backtest-stats">
                    <StatCard label="Total Return" value={`${backtestResult.total_return_pct >= 0 ? "+" : ""}${backtestResult.total_return_pct?.toFixed(2)}%`} color={backtestResult.total_return_pct >= 0 ? "#34d399" : "#f87171"} />
                    <StatCard label="Trades" value={backtestResult.total_trades} sub={`${backtestResult.winning_trades}W / ${backtestResult.losing_trades}L`} color="#60a5fa" />
                    <StatCard label="Win Rate" value={`${backtestResult.win_rate}%`} color="#fbbf24" />
                    <StatCard label="Final Value" value={formatCurrency(backtestResult.final_value, "USDT")} color="#a78bfa" />
                  </div>
                  {backtestResult.equity_curve?.length > 0 && (
                    <div className="fm-equity-chart">
                      <h5>Equity Curve</h5>
                      <EquityChart data={backtestResult.equity_curve} />
                    </div>
                  )}
                  {backtestResult.trades?.length > 0 && (
                    <div className="fm-trade-log">
                      <h5>Trade Log ({backtestResult.trades.length})</h5>
                      <div className="fm-tx-mini">
                        {backtestResult.trades.map((t, i) => (
                          <div key={i} className="fm-tx-row">
                            <span className={`fm-side-${t.side.toLowerCase()}`}>{t.side}</span>
                            <span>{formatCurrency(t.price, "USDT")}</span>
                            <span>{formatCrypto(t.qty)}</span>
                            <span style={{ color: t.pnl > 0 ? "#34d399" : t.pnl < 0 ? "#f87171" : "#94a3b8" }}>
                              {t.pnl != null ? `${t.pnl >= 0 ? "+" : ""}${formatCurrency(t.pnl, "USDT")}` : "—"}
                            </span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
              {backtestResult?.error && (
                <div className="fm-parse-result error">
                  <span className="fm-parse-icon">❌</span>
                  <span>{backtestResult.error}</span>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── ADD ── */}
        {activeTab === "add" && (
          <div className="fm-add">
            <h4>Manual Transaction</h4>
            <div className="fm-form">
              <label>Amount</label>
              <input className="fm-input" type="number" step="0.01" placeholder="0.00" value={formAmount} onChange={e => setFormAmount(e.target.value)} />
              <label>Merchant</label>
              <input className="fm-input" placeholder="e.g. Amazon, Starbucks" value={formMerchant} onChange={e => setFormMerchant(e.target.value)} />
              <label>Category</label>
              <select className="fm-select" value={formCategory} onChange={e => setFormCategory(e.target.value)}>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
              <label>Currency</label>
              <select className="fm-select" value={formCurrency} onChange={e => setFormCurrency(e.target.value)}>
                <option value="USD">USD ($)</option>
                <option value="INR">INR (₹)</option>
                <option value="EUR">EUR (€)</option>
                <option value="GBP">GBP (£)</option>
              </select>
              <button className="fm-btn fm-btn-primary" onClick={addTransaction}>Add Transaction</button>
            </div>
          </div>
        )}

        {/* ── AUTONOMOUS ── */}
        {activeTab === "autonomous" && (
          <div className="fm-autonomous">
            {/* Live Signal Card */}
            {liveSignal && liveSignal.strategy && (
              <div className="fm-section">
                <div className={`fm-signal-card fm-signal-${liveSignal.signal?.toLowerCase()}`}>
                  <div className="fm-signal-main">
                    <span className="fm-signal-label">Live Signal</span>
                    <span className="fm-signal-badge">{liveSignal.signal}</span>
                    <span className="fm-signal-strat">{liveSignal.strategy}</span>
                    {liveSignal.price != null && (
                      <span className="fm-signal-price">@ {formatCurrency(liveSignal.price, "USDT")}</span>
                    )}
                  </div>
                  <div className="fm-signal-meta">
                    <span>Score: {liveSignal.score?.toFixed(1)}</span>
                    <span>BTC-USDT</span>
                  </div>
                </div>
              </div>
            )}

            {/* Status Bar */}
            <div className="fm-section">
              <div className="fm-auto-header">
                <h4>🧠 Autonomous Trading Engine</h4>
                <div className="fm-auto-controls">
                  <label className="fm-toggle">
                    <input type="checkbox" checked={autoTradeEnabled} onChange={e => toggleAutoTrade(e.target.checked)} />
                    <span>Auto-paper-trade on signals</span>
                  </label>
                  <button className="fm-btn" onClick={forceGenerateStrategy} disabled={genLoading}>
                    {genLoading ? "Generating…" : "Generate Strategy Now"}
                  </button>
                  <button className="fm-btn" onClick={forceAutoPaperTrade}>Force Paper Trade</button>
                </div>
              </div>
              {ateStatus && (
                <div className="fm-auto-status">
                  <span className={`fm-auto-badge ${ateStatus.active ? "active" : "idle"}`}>
                    {ateStatus.active ? "● Running" : "○ Idle"}
                  </span>
                  <span className="fm-auto-stat">{ateStatus.strategy_count || 0} strategies</span>
                  <span className="fm-auto-stat">Best score: {ateStatus.best_score?.toFixed(1) || "—"}</span>
                  <span className="fm-auto-stat">Mode: {ateStatus.mode}</span>
                </div>
              )}
            </div>

            {/* Generated Strategies */}
            <div className="fm-section">
              <h4>Generated Strategies</h4>
              {genStrategies.length === 0 ? (
                <p className="fm-empty">No strategies generated yet. Click "Generate Strategy Now" or wait for LOVE to auto-generate.</p>
              ) : (
                <div className="fm-strat-list">
                  {genStrategies.map((s, i) => (
                    <div key={i} className={`fm-strat-card ${s.status}`}>
                      <div className="fm-strat-header">
                        <span className="fm-strat-name">{s.name}</span>
                        <span className="fm-strat-type">{s.logic_type}</span>
                        <span className={`fm-strat-status ${s.status}`}>{s.status}</span>
                      </div>
                      <p className="fm-strat-desc">{s.description}</p>
                      <div className="fm-strat-stats">
                        <span style={{ color: s.best_return >= 0 ? "#34d399" : "#f87171" }}>
                          Best: {s.best_return >= 0 ? "+" : ""}{s.best_return?.toFixed(2)}%
                        </span>
                        <span>Win Rate: {s.win_rate?.toFixed(1)}%</span>
                        <span>Trades: {s.total_trades}</span>
                        <span>Sharpe: {s.sharpe_estimate?.toFixed(2)}</span>
                        <span className="fm-strat-score">Score: {s.score?.toFixed(1)}</span>
                      </div>
                      {s.backtests?.length > 0 && (
                        <div className="fm-strat-backtests">
                          {s.backtests.slice(-1).map((bt, j) => (
                            <div key={j} className="fm-strat-bt">
                              <span>{bt.symbol}</span>
                              <span style={{ color: bt.total_return_pct >= 0 ? "#34d399" : "#f87171" }}>
                                {bt.total_return_pct >= 0 ? "+" : ""}{bt.total_return_pct?.toFixed(1)}%
                              </span>
                              <span>{bt.total_trades} trades</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Auto Trade Log */}
            {autoTrades.length > 0 && (
              <div className="fm-section">
                <h4>Auto Paper Trade Log</h4>
                <div className="fm-tx-mini">
                  {autoTrades.map((t, i) => (
                    <div key={i} className="fm-tx-row">
                      <span className={`fm-side-${t.signal?.toLowerCase()}`}>{t.signal}</span>
                      <span>{formatCrypto(t.qty)} {t.symbol}</span>
                      <span>{t.price ? formatCurrency(t.price, "USDT") : "—"}</span>
                      <span className="fm-tx-time">{t.timestamp ? new Date(t.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Evolution Log */}
            {evolutionLog.length > 0 && (
              <div className="fm-section">
                <h4>Strategy Evolution</h4>
                <div className="fm-tx-mini">
                  {evolutionLog.map((e, i) => (
                    <div key={i} className="fm-tx-row">
                      <span className="fm-strat-type">evolved</span>
                      <span>Child score: {e.child_score?.toFixed(1)}</span>
                      <span>Return: {e.result?.total_return_pct >= 0 ? "+" : ""}{e.result?.total_return_pct?.toFixed(1)}%</span>
                      <span className="fm-tx-time">{e.timestamp ? new Date(e.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : ""}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── LEARNED ── */}
        {activeTab === "learned" && (
          <div className="fm-learned">
            {/* Mood & Location */}
            <div className="fm-section">
              <div className="fm-learned-header">
                <h4>🔮 Autonomous Learning</h4>
                <span className="fm-learned-badge">Zero-touch</span>
              </div>
              {learnedMood && (
                <div className="fm-learned-mood">
                  <span className={`fm-mood-badge fm-mood-${learnedMood.mood}`}>
                    {learnedMood.mood === "stressed" ? "😰" : learnedMood.mood === "tense" ? "😬" : learnedMood.mood === "positive" ? "🙂" : "😐"} {learnedMood.mood}
                  </span>
                  <span className="fm-learned-stat">confidence: {(learnedMood.confidence * 100).toFixed(0)}%</span>
                  <span className="fm-learned-stat">stress: {learnedMood.stress_signals}</span>
                  <span className="fm-learned-stat">positive: {learnedMood.positive_signals}</span>
                </div>
              )}
              {learnedProfile && learnedProfile.known_locations && learnedProfile.known_locations.length > 0 && (
                <div className="fm-learned-locations">
                  <span className="fm-learned-label">Known locations:</span>
                  {learnedProfile.known_locations.map((loc, i) => (
                    <span key={i} className="fm-learned-chip">{loc}</span>
                  ))}
                </div>
              )}
            </div>

            {/* Merchants */}
            {learnedMerchants.length > 0 && (
              <div className="fm-section">
                <h4>Learned Merchants</h4>
                <div className="fm-learned-list">
                  {learnedMerchants.map(([merchant, count], i) => (
                    <div key={i} className="fm-learned-row">
                      <span className="fm-learned-name">{merchant}</span>
                      <span className="fm-learned-count">{count} txs</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Recurring Charges */}
            {learnedRecurring.length > 0 && (
              <div className="fm-section">
                <h4>Recurring Charges Detected</h4>
                <div className="fm-learned-list">
                  {learnedRecurring.map((rc, i) => (
                    <div key={i} className="fm-learned-row">
                      <span className="fm-learned-name">{rc.merchant}</span>
                      <span className="fm-learned-amount">~{formatCurrency(rc.amount, "INR")}</span>
                      <span className="fm-learned-count">{rc.count}x</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Anomalies */}
            {learnedAnomalies.length > 0 && (
              <div className="fm-section">
                <h4>🚨 Detected Anomalies</h4>
                <div className="fm-learned-list">
                  {learnedAnomalies.map((a, i) => (
                    <div key={i} className="fm-learned-row fm-learned-anomaly">
                      <span className="fm-learned-anomaly-text">{a.anomaly}</span>
                      <span className="fm-learned-anomaly-source">{a.app || "unknown"}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Suggestions */}
            {learnedSuggestions.length > 0 && (
              <div className="fm-section">
                <h4>💡 Autonomous Suggestions</h4>
                <div className="fm-learned-suggestions">
                  {learnedSuggestions.map((s, i) => (
                    <div key={i} className={`fm-suggestion fm-suggestion-${s.priority}`}>
                      <span className="fm-suggestion-icon">
                        {s.type === "upcoming_bill" ? "💳" : s.type === "location_prediction" ? "📍" : s.type === "mood_intervention" ? "🧘" : "💡"}
                      </span>
                      <span className="fm-suggestion-text">{s.message}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {!learnedProfile && learnedMerchants.length === 0 && learnedAnomalies.length === 0 && (
              <p className="fm-empty">LOVE is learning from your notifications. Check back after some activity.</p>
            )}
          </div>
        )}

        {/* ── PARSE ── */}
        {activeTab === "parse" && (
          <div className="fm-parse">
            <h4>Parse Bank Notification</h4>
            <p className="fm-hint">Paste a bank SMS or email snippet. LOVE will extract the amount, merchant, and category automatically.</p>
            <textarea className="fm-textarea" rows={4} placeholder="e.g. Your A/c XX1234 debited for Rs.2,450.00 on Swiggy. Avl Bal: Rs.12,340.50" value={parseText} onChange={e => setParseText(e.target.value)} />
            <button className="fm-btn fm-btn-primary" onClick={parseNotification}>Parse & Check</button>
            {parseResult && (
              <div className={`fm-parse-result ${parseResult.success ? "success" : "error"}`}>
                {parseResult.success ? (
                  <><span className="fm-parse-icon">✅</span><span>Parsed and checked. {parseResult.alerts?.length > 0 ? `${parseResult.alerts.length} alert(s) generated.` : "No alerts."}</span></>
                ) : (
                  <><span className="fm-parse-icon">❌</span><span>{parseResult.error || "Parse failed"}</span></>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Simple SVG equity chart
function EquityChart({ data }) {
  if (!data || data.length < 2) return null;
  const values = data.map(d => d.equity);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const width = 600;
  const height = 150;
  const padding = 10;
  const step = (width - padding * 2) / (values.length - 1);

  const points = values.map((v, i) => {
    const x = padding + i * step;
    const y = height - padding - ((v - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(" ");

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="fm-equity-svg">
      <polyline fill="none" stroke="#60a5fa" strokeWidth="2" points={points} />
      <circle cx={padding + (values.length - 1) * step} cy={height - padding - ((values[values.length - 1] - min) / range) * (height - padding * 2)} r="4" fill="#60a5fa" />
    </svg>
  );
}