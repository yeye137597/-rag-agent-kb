import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function UserManagement() {
  const [users, setUsers] = useState([])
  const [kbs, setKbs] = useState([])
  const [form, setForm] = useState({ username: '', password: '', role: 'user' })
  const [passwords, setPasswords] = useState({})
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      const [userItems, kbItems] = await Promise.all([api.listUsers(), api.listKbs()])
      setUsers(userItems)
      setKbs(kbItems)
    } catch (err) {
      setError(err.message || '加载用户失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function createUser() {
    setMessage('')
    setError('')
    try {
      await api.createUser(form)
      setForm({ username: '', password: '', role: 'user' })
      setMessage('用户已创建')
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function toggleActive(user) {
    setMessage('')
    setError('')
    try {
      await api.setUserActive(user.id, !user.is_active)
      setMessage('用户状态已更新')
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function resetPassword(userId) {
    setMessage('')
    setError('')
    try {
      await api.resetUserPassword(userId, passwords[userId] || '')
      setPasswords({ ...passwords, [userId]: '' })
      setMessage('密码已重置')
    } catch (err) {
      setError(err.message)
    }
  }

  async function savePermissions(userId, kbIds) {
    setMessage('')
    setError('')
    try {
      await api.updateUserPermissions(userId, kbIds)
      setMessage('知识库权限已保存')
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  function togglePermission(user, kbId) {
    const current = user.permissions || []
    const next = current.includes(kbId)
      ? current.filter((id) => id !== kbId)
      : [...current, kbId]
    setUsers(users.map((item) => (item.id === user.id ? { ...item, permissions: next } : item)))
  }

  return (
    <section className="panel">
      <div className="section-title">
        <h2>用户管理</h2>
        <button onClick={refresh} disabled={loading}>{loading ? '加载中...' : '刷新'}</button>
      </div>

      <div className="create-row">
        <input placeholder="用户名" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
        <input placeholder="密码" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
        <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
          <option value="user">user</option>
          <option value="admin">admin</option>
        </select>
        <button onClick={createUser} disabled={!form.username.trim() || !form.password}>创建用户</button>
      </div>

      {message && <div className="success">{message}</div>}
      {error && <div className="error">{error}</div>}

      <div className="user-list">
        {users.map((user) => (
          <article className="user-item" key={user.id}>
            <div>
              <h3>{user.username}</h3>
              <p className="muted">ID: {user.id} / {user.role} / {user.is_active ? '启用' : '禁用'}</p>
              <p className="muted">创建时间：{user.created_at || '-'}</p>
            </div>
            <div className="user-actions">
              <button onClick={() => toggleActive(user)}>{user.is_active ? '禁用' : '启用'}</button>
              <input
                type="password"
                placeholder="新密码"
                value={passwords[user.id] || ''}
                onChange={(event) => setPasswords({ ...passwords, [user.id]: event.target.value })}
              />
              <button onClick={() => resetPassword(user.id)}>重置密码</button>
            </div>
            {user.role === 'admin' ? (
              <p className="muted">管理员默认可访问全部知识库</p>
            ) : (
              <div className="permission-grid">
                {kbs.map((kb) => (
                  <label className="check-row" key={`${user.id}-${kb.id}`}>
                    <input
                      type="checkbox"
                      checked={(user.permissions || []).includes(kb.id)}
                      onChange={() => togglePermission(user, kb.id)}
                    />
                    <span>{kb.name}</span>
                    <small>{kb.id}</small>
                  </label>
                ))}
                <button onClick={() => savePermissions(user.id, user.permissions || [])}>保存授权</button>
              </div>
            )}
          </article>
        ))}
      </div>
    </section>
  )
}
