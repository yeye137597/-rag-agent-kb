import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function Chat() {
  const [kbs, setKbs] = useState([])
  const [selectedIds, setSelectedIds] = useState([])
  const [question, setQuestion] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [loadingKbs, setLoadingKbs] = useState(true)

  useEffect(() => {
    let ignore = false
    setLoadingKbs(true)
    api.listKbs()
      .then((items) => {
        if (ignore) return
        setKbs(Array.isArray(items) ? items : [])
        setSelectedIds(items?.[0] ? [items[0].id] : [])
      })
      .catch((err) => {
        if (!ignore) setError(err.message || '知识库列表加载失败')
      })
      .finally(() => {
        if (!ignore) setLoadingKbs(false)
      })
    return () => {
      ignore = true
    }
  }, [])

  function toggleKb(kbId) {
    setSelectedIds((current) => (
      current.includes(kbId)
        ? current.filter((id) => id !== kbId)
        : [...current, kbId]
    ))
  }

  async function ask() {
    setError('')
    setResult(null)
    setLoading(true)
    try {
      const data = await api.chat({ question, kb_ids: selectedIds })
      setResult(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="page-grid">
      <aside className="panel">
        <h2>选择知识库</h2>
        {loadingKbs && <p className="muted">知识库加载中...</p>}
        {!loadingKbs && kbs.length === 0 && <p className="muted">暂无可访问知识库</p>}
        {kbs.map((kb) => (
          <label className="check-row" key={kb.id}>
            <input
              type="checkbox"
              checked={selectedIds.includes(kb.id)}
              onChange={() => toggleKb(kb.id)}
            />
            <span>{kb.name}</span>
            <small>{kb.chunk_count} chunks</small>
          </label>
        ))}
      </aside>
      <section className="panel main-panel">
        <h2>知识库问答</h2>
        <textarea
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder="请输入你的问题"
          rows={5}
        />
        <div className="actions">
          <button onClick={ask} disabled={loading || !question.trim() || selectedIds.length === 0}>
            {loading ? '生成中...' : '提问'}
          </button>
        </div>
        {error && <div className="error">{error}</div>}
        {result && (
          <div className="answer">
            <h3>答案</h3>
            <div className="answer-text">{result.answer}</div>
            <div className="metrics">
              <span>耗时：{result.latency}s</span>
              <span>重试：{result.retry_count}</span>
              <span>资料充分：{result.is_enough ? '是' : '否'}</span>
            </div>
            {result.rewritten_question && <p className="muted">改写问题：{result.rewritten_question}</p>}
            {result.evaluation_reason && <p className="muted">评估原因：{result.evaluation_reason}</p>}
            <h3>引用来源</h3>
            {result.sources.map((source, index) => (
              <article className="source" key={`${source.metadata.source}-${index}`}>
                <strong>{source.metadata.kb_name || 'N/A'} / {source.metadata.source || 'N/A'}</strong>
                <small>page: {source.metadata.page || 'N/A'} | chunk: {source.metadata.chunk_id || 'N/A'}</small>
                <p>{source.content}</p>
              </article>
            ))}
          </div>
        )}
      </section>
    </section>
  )
}
