import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Logs({ user }) {
  const [tab, setTab] = useState(user.role === 'admin' ? 'audit' : 'queries')
  const [auditLogs, setAuditLogs] = useState([])
  const [queryLogs, setQueryLogs] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      if (user.role === 'admin' && tab === 'audit') {
        setAuditLogs(await api.auditLogs())
      } else {
        setQueryLogs(await api.queryLogs())
      }
    } catch (err) {
      setError(err.message || '日志加载失败，请稍后重试。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [tab])

  return (
    <section className="logs-page">
      <div className="logs-page-header">
        <div>
          <span className="eyebrow">系统审计</span>
          <h2>系统日志</h2>
          <p className="muted">查看用户登录、知识库操作、模型配置等系统行为记录。</p>
        </div>
        <button className="secondary-action" onClick={refresh} disabled={loading}>{loading ? '加载中...' : '刷新'}</button>
      </div>

      <div className="logs-tabs">
        {user.role === 'admin' && <button className={tab === 'audit' ? 'active' : ''} onClick={() => setTab('audit')}>审计日志</button>}
        <button className={tab === 'queries' ? 'active' : ''} onClick={() => setTab('queries')}>问答日志</button>
      </div>

      {error && <div className="chat-error-state logs-feedback" role="alert">{error}</div>}
      {loading && <div className="chat-loading-state logs-feedback" role="status">日志加载中...</div>}

      {tab === 'audit' && (
        <div className="logs-list">
          {!loading && auditLogs.length === 0 && <div className="chat-empty-state">暂无审计日志。</div>}
          {auditLogs.map((item, index) => (
            <article className="log-card" key={index}>
              <div className="log-card-header">
                <span className="log-type-pill">{item.action || '审计事件'}</span>
                <time>{item.created_at || '-'}</time>
              </div>
              <div className="log-meta-row">
                <span>用户：{item.username || '-'}</span>
              </div>
              <p className="log-detail">{item.detail || '-'}</p>
            </article>
          ))}
        </div>
      )}

      {tab === 'queries' && (
        <div className="logs-list">
          {!loading && queryLogs.length === 0 && <div className="chat-empty-state">暂无问答日志。</div>}
          {queryLogs.map((item, index) => (
            <article className="log-card" key={index}>
              <div className="log-card-header">
                <span className="log-type-pill">问答记录</span>
                <time>{item.time || '-'}</time>
              </div>
              <div className="log-meta-row">
                <span>用户：{item.username || '-'}</span>
                <span>耗时：{item.latency ?? '-'}s</span>
                <span>重试：{item.retry_count ?? '-'}</span>
              </div>
              <p className="log-detail">问题：{item.question || '-'}</p>
              <details className="log-detail-panel">
                <summary>查看答案和检索信息</summary>
                <pre>{item.answer || ''}</pre>
                <pre>{JSON.stringify({
                  selected_kbs: item.selected_kbs,
                  rewritten_question: item.rewritten_question,
                  evaluation_reason: item.evaluation_reason,
                  retrieved_docs: item.retrieved_docs,
                }, null, 2)}</pre>
              </details>
            </article>
          ))}
        </div>
      )}
    </section>
  )
}
