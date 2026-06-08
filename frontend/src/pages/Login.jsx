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
    <main className="login-page">
      <form className="login-panel" onSubmit={submit}>
        <h1>知识库问答系统</h1>
        <div className="tab-row">
          <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => switchMode('login')}>登录</button>
          <button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => switchMode('register')}>注册</button>
        </div>
        <label>
          用户名
          <input value={username} onChange={(event) => setUsername(event.target.value)} />
        </label>
        <label>
          密码
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
        </label>
        {mode === 'register' && (
          <label>
            确认密码
            <input type="password" value={confirmPassword} onChange={(event) => setConfirmPassword(event.target.value)} />
          </label>
        )}
        {message && <div className="success">{message}</div>}
        {error && <div className="error">{error}</div>}
        <button type="submit" disabled={loading}>
          {loading ? '处理中...' : mode === 'login' ? '登录' : '注册'}
        </button>
      </form>
    </main>
  )
}
