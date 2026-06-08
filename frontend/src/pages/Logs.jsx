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
      setError(err.message || '日志加载失败')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [tab])

  return (
    <section className="panel">
      <div className="section-title">
        <h2>日志</h2>
        <button onClick={refresh} disabled={loading}>{loading ? '加载中...' : '刷新'}</button>
      </div>
      <div className="tab-row">
        {user.role === 'admin' && <button className={tab === 'audit' ? 'active' : ''} onClick={() => setTab('audit')}>审计日志</button>}
        <button className={tab === 'queries' ? 'active' : ''} onClick={() => setTab('queries')}>问答日志</button>
      </div>
      {error && <div className="error">{error}</div>}

      {tab === 'audit' && (
        <div className="log-list">
          {auditLogs.map((item, index) => (
            <article className="log-item" key={index}>
              <strong>{item.created_at || '-'}</strong>
              <p>{item.username || '-'} / {item.action || '-'}</p>
              <p className="muted">{item.detail || '-'}</p>
            </article>
          ))}
        </div>
      )}

      {tab === 'queries' && (
        <div className="log-list">
          {queryLogs.map((item, index) => (
            <article className="log-item" key={index}>
              <strong>{item.time || '-'}</strong>
              <p>{item.username || '-'}：{item.question || '-'}</p>
              <p className="muted">耗时 {item.latency ?? '-'}s / 重试 {item.retry_count ?? '-'}</p>
              <details>
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
