import React, { useEffect, useState } from 'react'
import { api } from './api/client'
import Chat from './pages/Chat'
import KnowledgeBase from './pages/KnowledgeBase'
import Login from './pages/Login'
import Logs from './pages/Logs'
import ModelSettings from './pages/ModelSettings'
import UserManagement from './pages/UserManagement'

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <main className="login-page auth-page">
          <section className="login-panel auth-card">
            <h1>页面加载失败</h1>
            <div className="chat-error-state">{this.state.error.message || '前端运行时异常'}</div>
            <button className="primary-action" onClick={() => window.location.reload()}>刷新页面</button>
          </section>
        </main>
      )
    }
    return this.props.children
  }
}

function pageFromHash() {
  const hash = window.location.hash.replace('#', '')
  return hash || 'chat'
}

export default function App() {
  const [token, setToken] = useState(() => {
    try {
      return localStorage.getItem('token') || ''
    } catch {
      return ''
    }
  })
  const [user, setUser] = useState(null)
  const [page, setPage] = useState(pageFromHash)
  const [authError, setAuthError] = useState('')

  useEffect(() => {
    function syncPage() {
      setPage(pageFromHash())
    }
    window.addEventListener('hashchange', syncPage)
    return () => window.removeEventListener('hashchange', syncPage)
  }, [])

  useEffect(() => {
    if (!token) {
      setUser(null)
      return
    }
    api.setToken(token)
    api.me()
      .then((data) => {
        setUser(data)
        setAuthError('')
      })
      .catch((err) => {
        try {
          localStorage.removeItem('token')
        } catch {
          // ignore localStorage failures
        }
        setToken('')
        setUser(null)
        setAuthError(err.message || '登录状态已失效，请重新登录')
      })
  }, [token])

  function go(nextPage) {
    window.location.hash = nextPage
    setPage(nextPage)
  }

  function handleLogin(data) {
    try {
      localStorage.setItem('token', data.token)
    } catch {
      // token is still kept in memory for this session
    }
    api.setToken(data.token)
    setToken(data.token)
    setUser({ username: data.username, role: data.role, user_id: data.user_id })
    setAuthError('')
    go('chat')
  }

  function logout() {
    try {
      localStorage.removeItem('token')
    } catch {
      // ignore localStorage failures
    }
    api.setToken('')
    setToken('')
    setUser(null)
  }

  if (!token || !user) {
    return (
      <ErrorBoundary>
        <Login onLogin={handleLogin} initialError={authError} />
      </ErrorBoundary>
    )
  }

  return (
    <ErrorBoundary>
      <div className="app-shell">
        <header className="topbar app-topbar">
          <div className="topbar-brand">
            <span className="eyebrow">RAG Agent KB</span>
            <h1>知识库问答系统</h1>
            <span className="topbar-user">{user.username} / {user.role}</span>
          </div>
          <nav className="topbar-nav">
            <button className={page === 'chat' ? 'active' : ''} onClick={() => go('chat')}>问答</button>
            <button className={page === 'kb' ? 'active' : ''} onClick={() => go('kb')}>知识库</button>
            {user.role === 'admin' && (
              <button className={page === 'users' ? 'active' : ''} onClick={() => go('users')}>用户</button>
            )}
            {user.role === 'admin' && (
              <button className={page === 'models' ? 'active' : ''} onClick={() => go('models')}>模型设置</button>
            )}
            <button className={page === 'logs' ? 'active' : ''} onClick={() => go('logs')}>日志</button>
            <button className="logout-action" onClick={logout}>退出</button>
          </nav>
        </header>
        <main>
          {page === 'chat' && <Chat />}
          {page === 'kb' && <KnowledgeBase user={user} />}
          {page === 'users' && user.role === 'admin' && <UserManagement />}
          {page === 'models' && <ModelSettings user={user} />}
          {page === 'logs' && <Logs user={user} />}
          {!['chat', 'kb', 'users', 'models', 'logs'].includes(page) && <Chat />}
        </main>
      </div>
    </ErrorBoundary>
  )
}
