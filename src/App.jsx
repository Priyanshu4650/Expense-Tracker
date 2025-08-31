import { useState, useEffect } from 'react'
import './App.css'
import { FaMoneyBillWave, FaChartBar, FaChartLine, FaClock, FaFire, FaPlus, FaEdit, FaTrash, FaSave, FaTimes, FaBell, FaCheck, FaExclamationTriangle, FaSignOutAlt, FaLock, FaUserPlus, FaSignInAlt, FaUser, FaCalendarAlt, FaLightbulb } from 'react-icons/fa'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, BarChart, Bar } from 'recharts'

const formatCurrency = (amount) => `₹${parseFloat(amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
const getCurrentMonth = () => new Date().toISOString().slice(0, 7)

const AuthScreen = ({ authMode, authForm, setAuthForm, handleAuth, setAuthMode }) => (
  <div className="auth-screen">
    <div className="auth-modal">
      <h1><FaMoneyBillWave /> Expense Tracker</h1>
      <div className="auth-content">
        <h2>{authMode === 'login' ? <><FaLock /> Login</> : <><FaUserPlus /> Register</>}</h2>
        <form onSubmit={handleAuth} autoComplete="off">
          <input
            type="text"
            placeholder="Username"
            value={authForm.username}
            onChange={(e) => setAuthForm({ ...authForm, username: e.target.value })}
            required
            className="auth-input"
            autoComplete="off"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck="false"
          />
          <input
            type="password"
            placeholder="Password"
            value={authForm.password}
            onChange={(e) => setAuthForm({ ...authForm, password: e.target.value })}
            required
            className="auth-input"
            autoComplete="new-password"
            autoCorrect="off"
            autoCapitalize="off"
            spellCheck="false"
          />
          <button type="submit" className="btn btn-primary">
            {authMode === 'login' ? <><FaSignInAlt /> Login</> : <><FaUserPlus /> Register</>}
          </button>
        </form>
        <p>
          {authMode === 'login' ? "Don't have an account?" : "Already have an account?"}
          <button
            className="link-btn"
            onClick={() => setAuthMode(authMode === 'login' ? 'register' : 'login')}
          >
            {authMode === 'login' ? 'Register' : 'Login'}
          </button>
        </p>
      </div>
    </div>
  </div>
)

const PermissionScreen = ({ requestNotificationPermission, setShowPermissionModal }) => (
  <div className="permission-screen">
    <div className="permission-modal">
      <h1><FaMoneyBillWave /> Expense Tracker</h1>
      <div className="permission-content">
        <h2><FaBell /> Enable Notifications</h2>
        <p>This app needs notification permission to:</p>
        <ul>
          <li><FaCalendarAlt /> Remind you to set monthly budgets</li>
          <li><FaExclamationTriangle /> Alert when you exceed spending limits</li>
          <li><FaLightbulb /> Provide financial insights</li>
        </ul>
        <div className="permission-actions">
          <button className="btn btn-primary" onClick={requestNotificationPermission}>
            <FaCheck /> Allow Notifications
          </button>
          <button className="btn btn-secondary" onClick={() => setShowPermissionModal(false)}>
            <FaTimes /> Continue Without Notifications
          </button>
        </div>
      </div>
    </div>
  </div>
)

function App() {
  const [expenses, setExpenses] = useState([])
  const [summary, setSummary] = useState({ total: 0, categories: {} })
  const [categories, setCategories] = useState([])
  const [formData, setFormData] = useState({ category: '', amount: '', description: '', payment_date: new Date().toISOString().split('T')[0] })
  const [newCategory, setNewCategory] = useState('')
  const [editingId, setEditingId] = useState(null)
  const [analytics, setAnalytics] = useState(null)
  const [showDashboard, setShowDashboard] = useState(false)
  const [budgets, setBudgets] = useState({})
  const [budgetStatus, setBudgetStatus] = useState({})
  const [showPlanModal, setShowPlanModal] = useState(false)
  const [monthlyPlan, setMonthlyPlan] = useState({ income: '', budgets: {} })
  const [currentIncome, setCurrentIncome] = useState(0)
  const [hasExistingPlan, setHasExistingPlan] = useState(false)
  const [notificationPermission, setNotificationPermission] = useState('default')
  const [showPermissionModal, setShowPermissionModal] = useState(true)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  const [authMode, setAuthMode] = useState('login')
  const [authForm, setAuthForm] = useState({ username: '', password: '' })
  const [token, setToken] = useState(localStorage.getItem('token'))

  useEffect(() => {
    if (token) {
      setIsAuthenticated(true)
      checkNotificationPermission()
    } else {
      setShowAuthModal(true)
    }
  }, [])

  useEffect(() => {
    if (isAuthenticated && notificationPermission === 'granted') {
      fetchCategories()
      fetchExpenses()
      fetchSummary()
      fetchAnalytics()
      checkMonthlyBudget()
      setupMonthlyNotification()
    }
  }, [notificationPermission, isAuthenticated])

  // Auto logout after 24 hours
  useEffect(() => {
    if (token) {
      const timeout = setTimeout(() => {
        handleLogout()
      }, 24 * 60 * 60 * 1000) // 24 hours
      return () => clearTimeout(timeout)
    }
  }, [token])

  // Keep server alive with health checks
  useEffect(() => {
    const keepAlive = setInterval(() => {
      fetch('https://expense-tracker-1-frb7.onrender.com/health')
        .catch(() => {}) // Ignore errors
    }, 10 * 60 * 1000) // Every 10 minutes
    
    return () => clearInterval(keepAlive)
  }, [])

  const checkNotificationPermission = () => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission)
      if (Notification.permission === 'granted') {
        setShowPermissionModal(false)
      }
    } else {
      setNotificationPermission('denied')
    }
  }

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission()
      setNotificationPermission(permission)
      if (permission === 'granted') {
        setShowPermissionModal(false)
      }
    }
  }

  const setupMonthlyNotification = () => {
    // Check every hour if it's the 1st of the month
    const checkInterval = setInterval(() => {
      const now = new Date()
      if (now.getDate() === 1 && now.getHours() === 9) { // 9 AM on 1st
        const currentMonth = getCurrentMonth()
        fetchMonthlyPlan(currentMonth).then(plan => {
          if (!plan?.income || Object.keys(plan.budgets).length === 0) {
            showMonthlyPlanNotification()
          }
        })
      }
    }, 3600000) // Check every hour

    return () => clearInterval(checkInterval)
  }

  const showMonthlyPlanNotification = () => {
    if (notificationPermission === 'granted') {
      const notification = new Notification('Monthly Planning Time!', {
        body: 'Set your income and expenditure plan for this month',
        icon: '/vite.svg',
        tag: 'monthly-plan',
        requireInteraction: true
      })

      notification.onclick = () => {
        window.focus()
        setShowPlanModal(true)
        notification.close()
      }
    }
  }

  const showNotification = (title, body) => {
    if ('Notification' in window && Notification.permission === 'granted') {
      new Notification(title, { body, icon: '/vite.svg' })
    }
  }

  const checkMonthlyBudget = async () => {
    const currentMonth = getCurrentMonth()
    const today = new Date()

    // Check if it's the 1st of the month
    if (today.getDate() === 1) {
      const planExists = await fetchMonthlyPlan(currentMonth)
      if (!planExists?.income || Object.keys(planExists.budgets).length === 0) {
        showMonthlyPlanNotification()
      }
    }

    // Fetch current plan and budget status
    await fetchMonthlyPlan(currentMonth)
    fetchBudgetStatus(currentMonth)
  }

  const fetchMonthlyPlan = async (month) => {
    try {
      const response = await fetch(`https://expense-tracker-1-frb7.onrender.com/api/budget/monthly-plan/${month}`, {
        headers: getAuthHeaders()
      })
      const data = await response.json()
      setBudgets(data.budgets)
      setCurrentIncome(data.income)
      setHasExistingPlan(data.income > 0 || Object.keys(data.budgets).length > 0)
      return data
    } catch (error) {
      console.error('Error fetching monthly plan:', error)
      return { income: 0, budgets: {} }
    }
  }

  const fetchBudgetStatus = async (month) => {
    try {
      const response = await fetch(`https://expense-tracker-1-frb7.onrender.com/api/budget/budget-status/${month}`, {
        headers: getAuthHeaders()
      })
      const data = await response.json()
      setBudgetStatus(data)
    } catch (error) {
      console.error('Error fetching budget status:', error)
    }
  }

  const fetchAnalytics = async () => {
    try {
      const response = await fetch('https://expense-tracker-1-frb7.onrender.com/api/expenses/analytics', {
        headers: getAuthHeaders()
      })
      const data = await response.json()
      setAnalytics(data)
    } catch (error) {
      console.error('Error fetching analytics:', error)
    }
  }

  const getAuthHeaders = () => ({
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  })

  const handleAuth = async (e) => {
    e.preventDefault()
    try {
      const endpoint = authMode === 'login' ? 'login' : 'register'
      const response = await fetch(`https://expense-tracker-1-frb7.onrender.com/api/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(authForm)
      })

      if (response.ok) {
        const data = await response.json()
        if (authMode === 'login') {
          localStorage.setItem('token', data.access_token)
          setToken(data.access_token)
          setIsAuthenticated(true)
          setShowAuthModal(false)
          checkNotificationPermission()
        } else {
          setAuthMode('login')
          alert('Registration successful! Please login.')
        }
      } else {
        const error = await response.json()
        alert(error.detail)
      }
    } catch (error) {
      console.error('Auth error:', error)
    }
    setAuthForm({ username: '', password: '' })
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setIsAuthenticated(false)
    setShowAuthModal(true)
    // Reset all state
    setExpenses([])
    setSummary({ total: 0, categories: {} })
    setCategories([])
    setAnalytics(null)
  }

  const fetchCategories = async () => {
    try {
      const response = await fetch('https://expense-tracker-1-frb7.onrender.com/api/categories', {
        headers: getAuthHeaders()
      })
      if (response.status === 401) {
        handleLogout()
        return
      }
      const data = await response.json()
      setCategories(data)
      if (data.length > 0 && !formData.category) {
        setFormData(prev => ({ ...prev, category: data[0] }))
      }
    } catch (error) {
      console.error('Error fetching categories:', error)
    }
  }

  const fetchExpenses = async () => {
    try {
      const response = await fetch('https://expense-tracker-1-frb7.onrender.com/api/expenses', {
        headers: getAuthHeaders()
      })
      if (response.status === 401) {
        handleLogout()
        return
      }
      const data = await response.json()
      setExpenses(data)
    } catch (error) {
      console.error('Error fetching expenses:', error)
    }
  }

  const fetchSummary = async () => {
    try {
      const response = await fetch('https://expense-tracker-1-frb7.onrender.com/api/expenses/summary', {
        headers: getAuthHeaders()
      })
      if (response.status === 401) {
        handleLogout()
        return
      }
      const data = await response.json()
      setSummary(data)
    } catch (error) {
      console.error('Error fetching summary:', error)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      const response = await fetch('https://expense-tracker-1-frb7.onrender.com/api/expenses', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ ...formData, amount: parseFloat(formData.amount) })
      })
      if (response.status === 401) {
        handleLogout()
        return
      }
      setFormData({ category: categories[0] || '', amount: '', description: '', payment_date: new Date().toISOString().split('T')[0] })
      fetchExpenses()
      fetchSummary()
      fetchAnalytics()

      // Check budget after adding expense
      const currentMonth = getCurrentMonth()
      await fetchBudgetStatus(currentMonth)
      await fetchMonthlyPlan(currentMonth)
      checkBudgetNotifications(formData.category, parseFloat(formData.amount))
    } catch (error) {
      console.error('Error adding expense:', error)
    }
  }

  const checkBudgetNotifications = (category, amount) => {
    const status = budgetStatus[category]
    if (status) {
      const newSpent = status.spent + amount
      const newPercentage = (newSpent / status.budget) * 100

      if (newPercentage >= 100) {
        const exceeded = newSpent - status.budget
        showNotification('Budget Exceeded!', `${category}: Exceeded by ${formatCurrency(exceeded)}`)
      } else if (newPercentage >= 80) {
        const remaining = status.budget - newSpent
        showNotification('Budget Warning!', `${category}: Only ${formatCurrency(remaining)} remaining`)
      }
    }
  }

  const handleSetMonthlyPlan = async (e) => {
    e.preventDefault()
    const totalPlanned = Object.values(monthlyPlan.budgets).reduce((sum, amount) => sum + (amount || 0), 0)
    const income = parseFloat(monthlyPlan.income)

    if (totalPlanned > income) {
      alert(`Warning: Total planned expenditure (₹${totalPlanned}) exceeds income (₹${income})!`)
    }

    try {
      await fetch('https://expense-tracker-1-frb7.onrender.com/api/budget/monthly-plan', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          month: getCurrentMonth(),
          income: income,
          budgets: monthlyPlan.budgets
        })
      })
      setShowPlanModal(false)
      setMonthlyPlan({ income: '', budgets: {} })
      fetchMonthlyPlan(getCurrentMonth())
      fetchBudgetStatus(getCurrentMonth())
      showNotification(hasExistingPlan ? 'Monthly Plan Updated!' : 'Monthly Plan Set!', `Income: ₹${income}, Total Budget: ₹${totalPlanned}`)
    } catch (error) {
      console.error('Error setting monthly plan:', error)
    }
  }

  const handleAddCategory = async (e) => {
    e.preventDefault()
    if (!newCategory.trim()) return
    try {
      await fetch('https://expense-tracker-1-frb7.onrender.com/api/categories', {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ name: newCategory })
      })
      setNewCategory('')
      fetchCategories()
    } catch (error) {
      console.error('Error adding category:', error)
    }
  }

  const handleEdit = (expense) => {
    setEditingId(expense.id)
    setFormData({ 
      category: expense.category, 
      amount: expense.amount.toString(), 
      description: expense.description,
      payment_date: expense.payment_date || new Date().toISOString().split('T')[0]
    })
  }

  const handleUpdate = async (e) => {
    e.preventDefault()
    try {
      await fetch(`https://expense-tracker-1-frb7.onrender.com/api/expenses/${editingId}`, {
        method: 'PUT',
        headers: getAuthHeaders(),
        body: JSON.stringify({ ...formData, amount: parseFloat(formData.amount) })
      })
      setEditingId(null)
      setFormData({ category: categories[0] || '', amount: '', description: '', payment_date: new Date().toISOString().split('T')[0] })
      fetchExpenses()
      fetchSummary()
      fetchAnalytics()
    } catch (error) {
      console.error('Error updating expense:', error)
    }
  }

  const handleDelete = async (id) => {
    if (!confirm('Are you sure you want to delete this expense?')) return
    try {
      await fetch(`https://expense-tracker-1-frb7.onrender.com/api/expenses/${id}`, {
        method: 'DELETE',
        headers: getAuthHeaders()
      })
      fetchExpenses()
      fetchSummary()
      fetchAnalytics()
    } catch (error) {
      console.error('Error deleting expense:', error)
    }
  }

  const handleCancel = () => {
    setEditingId(null)
    setFormData({ category: categories[0] || '', amount: '', description: '', payment_date: new Date().toISOString().split('T')[0] })
  }

  if (showAuthModal) {
    return <AuthScreen authMode={authMode} authForm={authForm} setAuthForm={setAuthForm} handleAuth={handleAuth} setAuthMode={setAuthMode} />
  }

  if (showPermissionModal) {
    return <PermissionScreen requestNotificationPermission={requestNotificationPermission} setShowPermissionModal={setShowPermissionModal} />
  }

  return (
    <div className="app">
      <header className="header">
        <h1><FaMoneyBillWave /> Expense Tracker</h1>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn btn-secondary" onClick={() => {
            if (hasExistingPlan) {
              setMonthlyPlan({
                income: currentIncome.toString(),
                budgets: { ...budgets }
              })
            } else {
              setMonthlyPlan({ income: '', budgets: {} })
            }
            setShowPlanModal(true)
          }}><FaMoneyBillWave /> {hasExistingPlan ? 'Edit Plan' : 'Monthly Plan'}</button>
          {notificationPermission !== 'granted' && (
            <button className="btn btn-warning" onClick={requestNotificationPermission}><FaBell /> Enable Notifications</button>
          )}
          <button className="btn btn-secondary" onClick={handleLogout}><FaSignOutAlt /> Logout</button>
        </div>
      </header>

      <div className="main-layout">
        {analytics && (
          <div className="sidebar">
            <h2><FaChartBar /> Analytics</h2>
            <div className="chart-card">
              <h3><FaChartLine /> Monthly Trends</h3>
              <ResponsiveContainer width="100%" height={180}>
                <LineChart data={[...analytics.monthly_trends].reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" fontSize={10} />
                  <YAxis fontSize={10} />
                  <Tooltip formatter={(value) => [formatCurrency(value), 'Amount']} />
                  <Line type="monotone" dataKey="total" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3><FaChartBar /> Categories</h3>
              <ResponsiveContainer width="100%" height={180}>
                <PieChart>
                  <Pie
                    data={analytics.category_breakdown}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ category, percent }) => `${category} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={60}
                    fill="#8884d8"
                    dataKey="total"
                    fontSize={8}
                  >
                    {analytics.category_breakdown.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'][index % 5]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [formatCurrency(value), 'Amount']} />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="chart-card">
              <h3><FaClock /> Daily Activity</h3>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={[...analytics.recent_activity].reverse()}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={(date) => new Date(date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric' })} fontSize={10} />
                  <YAxis fontSize={10} />
                  <Tooltip formatter={(value) => [formatCurrency(value), 'Amount']} labelFormatter={(date) => new Date(date).toLocaleDateString('en-IN')} />
                  <Bar dataKey="total" fill="#82ca9d" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        <div className="content">
          <div className="summary-cards">
            <div className="summary-card income">
              <span className="label">Monthly Income</span>
              <span className="value">{formatCurrency(currentIncome)}</span>
            </div>
            <div className="summary-card total">
              <span className="label">Total Spent</span>
              <span className="value">{formatCurrency(summary.total)}</span>
              <div className="budget-info">
                <small>Remaining: {formatCurrency(currentIncome - summary.total)}</small>
              </div>
            </div>
            {categories.map(cat => {
              const status = budgetStatus[cat]
              const spent = summary.categories[cat] || 0
              const isOverBudget = status && spent > status.budget
              return (
                <div key={cat} className={`summary-card ${isOverBudget ? 'over-budget' : ''}`}>
                  <span className="label">{cat}</span>
                  <span className="value">{formatCurrency(spent)}</span>
                  {status && (
                    <div className="budget-info">
                      <small>Budget: {formatCurrency(status.budget)}</small>
                      <div className="progress-bar">
                        <div className="progress" style={{ width: `${Math.min(status.percentage, 100)}%` }}></div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>

          <div className="forms-section">
            <form onSubmit={handleAddCategory} className="form category-form">
              <input
                className="input"
                type="text"
                placeholder="Add new category"
                value={newCategory}
                onChange={(e) => setNewCategory(e.target.value)}
              />
              <button type="submit" className="btn btn-secondary"><FaPlus /> Add</button>
            </form>

            <form onSubmit={editingId ? handleUpdate : handleSubmit} className="form expense-form">
              <select className="select" value={formData.category} onChange={(e) => setFormData({ ...formData, category: e.target.value })}>
                {categories.map(cat => <option key={cat} value={cat}>{cat}</option>)}
              </select>
              <input
                className="input"
                type="number"
                placeholder="Amount (₹)"
                value={formData.amount}
                onChange={(e) => setFormData({ ...formData, amount: e.target.value })}
                required
              />
              <input
                className="input"
                type="text"
                placeholder="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              />
              <input
                className="input"
                type="date"
                value={formData.payment_date}
                onChange={(e) => setFormData({ ...formData, payment_date: e.target.value })}
                required
              />
              <button type="submit" className="btn btn-primary">
                {editingId ? <><FaEdit /> Update</> : <><FaPlus /> Add</>} Expense
              </button>
              {editingId && <button type="button" className="btn btn-secondary" onClick={handleCancel}><FaTimes /> Cancel</button>}
            </form>
          </div>

          <div className="expenses-section">
            <h2><FaMoneyBillWave /> Your Expenses</h2>
            <div className="expenses-list">
              {expenses.map(expense => (
                <div key={expense.id} className="expense-row">
                  <div className="expense-info">
                    <div className="expense-header">
                      <span className="category-tag">{expense.category}</span>
                      <span className="amount">{formatCurrency(expense.amount)}</span>
                    </div>
                    <div className="expense-details">
                      <span className="description">{expense.description}</span>
                      <span className="date">{new Date(expense.payment_date || expense.created_at).toLocaleDateString('en-IN')}</span>
                    </div>
                  </div>
                  <div className="expense-actions">
                    <button className="btn-icon" onClick={() => handleEdit(expense)} title="Edit"><FaEdit /></button>
                    <button className="btn-icon" onClick={() => handleDelete(expense.id)} title="Delete"><FaTrash /></button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {showPlanModal && (
        <div className="modal-overlay" onClick={() => setShowPlanModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h3><FaMoneyBillWave /> {hasExistingPlan ? 'Edit Monthly Plan' : 'Monthly Income & Expenditure Plan'}</h3>
            <form onSubmit={handleSetMonthlyPlan}>
              <div className="income-section">
                <h4><FaMoneyBillWave /> Monthly Income</h4>
                <input
                  type="number"
                  placeholder="Enter your monthly income"
                  value={monthlyPlan.income}
                  onChange={(e) => setMonthlyPlan({ ...monthlyPlan, income: e.target.value })}
                  required
                  className="income-input"
                />
              </div>

              <div className="budget-section">
                <h4><FaChartBar /> Planned Expenditure by Category</h4>
                {categories.map(cat => (
                  <div key={cat} className="budget-input">
                    <label>{cat}:</label>
                    <input
                      type="number"
                      placeholder="Planned amount"
                      value={monthlyPlan.budgets[cat] || ''}
                      onChange={(e) => setMonthlyPlan({
                        ...monthlyPlan,
                        budgets: { ...monthlyPlan.budgets, [cat]: parseFloat(e.target.value) || 0 }
                      })}
                      required
                    />
                  </div>
                ))}

                <div className="plan-summary">
                  <div className="summary-row">
                    <span>Total Income:</span>
                    <span>{formatCurrency(parseFloat(monthlyPlan.income) || 0)}</span>
                  </div>
                  <div className="summary-row">
                    <span>Total Planned:</span>
                    <span>{formatCurrency(Object.values(monthlyPlan.budgets).reduce((sum, amount) => sum + (amount || 0), 0))}</span>
                  </div>
                  <div className="summary-row savings">
                    <span>Expected Savings:</span>
                    <span>{formatCurrency((parseFloat(monthlyPlan.income) || 0) - Object.values(monthlyPlan.budgets).reduce((sum, amount) => sum + (amount || 0), 0))}</span>
                  </div>
                </div>
              </div>

              <div className="modal-actions">
                <button type="submit" className="btn btn-primary"><FaSave /> {hasExistingPlan ? 'Update Plan' : 'Save Plan'}</button>
                <button type="button" className="btn btn-secondary" onClick={() => setShowPlanModal(false)}><FaTimes /> Cancel</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}

export default App