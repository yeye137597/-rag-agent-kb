import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Login({ onLogin, initialError = '' }) {
  const [mode, setMode] = useState('login')
  const [username, setUsername] = useState('admin')
  const [password, setPassword] = useState('admin123')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState(initialError)
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    setError(initialError)
  }, [initialError])

  async function submit(event) {
    event.preventDefault()
    setError('')
    setMessage('')
    setLoading(true)
    try {
      if (mode === 'register') {
        if (password !== confirmPassword) {
          throw new Error('两次输入的密码不一致')
        }
        const data = await api.register({ username, password })
        setMessage(data.message || '注册成功，请登录')
        setMode('login')
        return
      }
      const data = await api.login({ username, password })
      onLogin(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  function switchMode(nextMode) {
    setMode(nextMode)
    setError('')
    setMessage('')
    if (nextMode === 'login') {
      setUsername('admin')
      setPassword('admin123')
    } else {
      setUsername('')
      setPassword('')
      setConfirmPassword('')
    }
  }

  return (
    <main className="login-page auth-page">
      <div className="login-container">

        {/* Left: Product intro */}
        <section className="login-hero">
          <div className="login-hero-body">
            <span className="eyebrow">RAG Agent KB</span>
            <h1 className="login-hero-title">知识库问答系统</h1>
            <p className="login-hero-subtitle">面向个人资料管理的 RAG 知识库问答与检索增强系统。</p>

            <div className="login-feature-list">
              <div className="login-feature-item">
                <span className="login-feature-dot" />
                <span>多知识库管理</span>
              </div>
              <div className="login-feature-item">
                <span className="login-feature-dot" />
                <span>文档清洗与向量构建</span>
              </div>
              <div className="login-feature-item">
                <span className="login-feature-dot" />
                <span>基于引用来源的智能问答</span>
              </div>
            </div>

            <div className="login-spec-card">
              <div className="login-spec-row">
                <span className="login-spec-label">支持格式</span>
                <span className="login-spec-value">PDF / DOCX / Markdown / TXT</span>
              </div>
              <div className="login-spec-row">
                <span className="login-spec-label">模型配置</span>
                <span className="login-spec-value">LLM 与 Embedding 自定义</span>
              </div>
              <div className="login-spec-row">
                <span className="login-spec-label">权限管理</span>
                <span className="login-spec-value">用户权限与操作日志</span>
              </div>
            </div>
          </div>

          {/* Decorative background circles */}
          <div className="login-hero-bg">
            <span className="login-circle login-circle-1" />
            <span className="login-circle login-circle-2" />
            <span className="login-circle login-circle-3" />
          </div>
        </section>

        {/* Right: Login card */}
        <section className="login-card-section">
          <form className="auth-card login-auth-card" onSubmit={submit}>
            <div className="auth-heading">
              <span className="login-card-label">
                {mode === 'login' ? '欢迎回来' : '创建账号'}
              </span>
              <h1>{mode === 'login' ? '登录到控制台' : '注册新账号'}</h1>
              <p className="muted">
                {mode === 'login'
                  ? '使用您的账号密码登录系统'
                  : '创建一个新账号以访问系统'}
              </p>
            </div>

            <div className="auth-tabs">
              <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => switchMode('login')}>登录</button>
              <button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => switchMode('register')}>注册</button>
            </div>

            <label className="auth-field">
              <span>用户名</span>
              <input value={username} onChange={(event) => setUsername(event.target.value)} placeholder="请输入用户名" />
            </label>
            <label className="auth-field">
              <span>密码</span>
              <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="请输入密码" />
            </label>
            {mode === 'register' && (
              <label className="auth-field">
                <span>确认密码</span>
                <input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} placeholder="请再次输入密码" />
              </label>
            )}
            {message && <div className="success auth-feedback">{message}</div>}
            {error && <div className="chat-error-state auth-feedback" role="alert">{error}</div>}
            <button className="primary-action auth-submit" type="submit" disabled={loading}>
              {loading ? '处理中...' : mode === 'login' ? '登录' : '注册'}
            </button>
          </form>
        </section>

      </div>
    </main>
  )
}
