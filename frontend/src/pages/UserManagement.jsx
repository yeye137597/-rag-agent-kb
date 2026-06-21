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
  const [expandedUserIds, setExpandedUserIds] = useState({})

  function toggleExpanded(userId) {
    setExpandedUserIds((current) => ({ ...current, [userId]: !current[userId] }))
  }

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      const [userItems, kbItems] = await Promise.all([api.listUsers(), api.listKbs()])
      setUsers(userItems)
      setKbs(kbItems)
    } catch (err) {
      setError(err.message || '加载用户失败，请稍后重试。')
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
    <section className="user-page">
      <div className="user-page-header">
        <div>
          <span className="eyebrow">用户与权限</span>
          <h2>用户管理</h2>
          <p className="muted">创建用户、管理账号状态，并配置知识库访问权限。</p>
        </div>
        <button className="secondary-action" onClick={refresh} disabled={loading}>{loading ? '加载中...' : '刷新'}</button>
      </div>

      <div className="user-create-card">
        <div>
          <h3>创建用户</h3>
          <p className="muted">为团队成员创建账号，并指定初始角色。</p>
        </div>
        <div className="user-create-form">
          <input placeholder="用户名" value={form.username} onChange={(event) => setForm({ ...form, username: event.target.value })} />
          <input placeholder="密码" type="password" value={form.password} onChange={(event) => setForm({ ...form, password: event.target.value })} />
          <select value={form.role} onChange={(event) => setForm({ ...form, role: event.target.value })}>
            <option value="user">普通用户</option>
            <option value="admin">管理员</option>
          </select>
          <button className="primary-action" onClick={createUser} disabled={!form.username.trim() || !form.password}>创建用户</button>
        </div>
      </div>

      {message && <div className="success user-feedback">{message}</div>}
      {error && <div className="chat-error-state user-feedback" role="alert">{error}</div>}
      {loading && <div className="chat-loading-state user-feedback" role="status">用户列表加载中...</div>}
      {!loading && users.length === 0 && (
        <div className="chat-empty-state user-feedback">暂无用户。请先创建一个用户账号。</div>
      )}

      <div className="user-card-list">
        {users.map((user) => {
          const isExpanded = !!expandedUserIds[user.id]
          return (
            <article className="user-manage-card" key={user.id}>
              <div className="user-card-header">
                <div className="user-card-title-group">
                  <h3>{user.username}</h3>
                  <p className="muted">用户 ID：{user.id} &middot; 创建时间：{user.created_at || '-'}</p>
                </div>
                <div className="user-card-actions">
                  <div className="user-badge-row">
                    <span>{user.role === 'admin' ? '管理员' : '普通用户'}</span>
                    <span className={user.is_active ? 'is-active' : 'is-disabled'}>{user.is_active ? '已启用' : '已禁用'}</span>
                  </div>
                  <button className="secondary-action user-expand-btn" onClick={() => toggleExpanded(user.id)}>
                    {isExpanded ? '收起' : '展开管理'}
                  </button>
                </div>
              </div>

              {isExpanded && (
                <div className="user-section-grid">
                  <section className="user-operation-section">
                    <div className="user-section-heading">
                      <h4>账号操作</h4>
                      <p className="muted">管理账号状态，或为用户设置新密码。</p>
                    </div>
                    <div className="user-account-actions">
                      <button className="secondary-action" onClick={() => toggleActive(user)}>{user.is_active ? '禁用' : '启用'}</button>
                      <input
                        type="password"
                        placeholder="新密码"
                        value={passwords[user.id] || ''}
                        onChange={(event) => setPasswords({ ...passwords, [user.id]: event.target.value })}
                      />
                      <button className="secondary-action" onClick={() => resetPassword(user.id)}>重置密码</button>
                    </div>
                  </section>

                  {user.role === 'admin' ? (
                    <section className="user-operation-section">
                      <div className="user-section-heading">
                        <h4>授权设置</h4>
                        <p className="muted">管理员默认可访问全部知识库。</p>
                      </div>
                    </section>
                  ) : (
                    <section className="user-operation-section">
                      <div className="user-section-heading">
                        <h4>授权设置</h4>
                        <p className="muted">选择该用户可以访问的知识库。</p>
                      </div>
                      {kbs.length === 0 ? (
                        <div className="chat-empty-state">暂无可授权知识库。</div>
                      ) : (
                        <div className="user-permission-list">
                          {kbs.map((kb) => (
                            <label className="permission-card" key={`${user.id}-${kb.id}`}>
                              <input
                                type="checkbox"
                                checked={(user.permissions || []).includes(kb.id)}
                                onChange={() => togglePermission(user, kb.id)}
                              />
                              <span>
                                <strong>{kb.name}</strong>
                                <small>{kb.id}</small>
                              </span>
                            </label>
                          ))}
                        </div>
                      )}
                      <div className="user-permission-footer">
                        <button className="primary-action" onClick={() => savePermissions(user.id, user.permissions || [])}>保存授权</button>
                      </div>
                    </section>
                  )}
                </div>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}
