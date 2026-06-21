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
  const hasQuestion = question.trim().length > 0
  const hasSelectedKb = selectedIds.length > 0
  const sources = result?.sources || []

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
        if (!ignore) setError(err.message || '知识库列表加载失败，请稍后重试。')
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
    <section className="chat-page">
      <aside className="panel chat-sidebar">
        <div className="chat-section-heading">
          <span className="eyebrow">步骤 1</span>
          <h2>选择知识库</h2>
          <p className="muted">选择一个或多个知识库，系统会基于这些资料生成回答。</p>
        </div>

        {loadingKbs && <div className="chat-state">知识库加载中...</div>}
        {!loadingKbs && kbs.length === 0 && (
          <div className="chat-empty-state">暂无可访问知识库，请先到知识库管理页面创建或上传资料。</div>
        )}
        <div className="kb-picker-list">
          {kbs.map((kb) => (
            <label className={`kb-picker-card ${selectedIds.includes(kb.id) ? 'is-selected' : ''}`} key={kb.id}>
              <input
                type="checkbox"
                checked={selectedIds.includes(kb.id)}
                onChange={() => toggleKb(kb.id)}
              />
              <span className="kb-picker-main">
                <strong>{kb.name}</strong>
                <small>{kb.chunk_count} 片段</small>
              </span>
            </label>
          ))}
        </div>
      </aside>

      <section className="panel main-panel chat-main">
        <div className="chat-hero">
          <span className="eyebrow">步骤 2</span>
          <h2>知识库问答</h2>
          <p className="muted">输入问题后，系统会先检索知识库，再生成带引用来源的答案。</p>
        </div>

        <div className="question-card">
          <label className="question-label" htmlFor="chat-question">输入问题</label>
          <textarea
            id="chat-question"
            className="question-input"
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="请输入你的问题，例如：这个项目的核心功能是什么？"
            rows={5}
          />
          <div className="question-footer">
            <div className="question-hints">
              {!hasQuestion && <p className="muted helper-text">请输入问题后再提问</p>}
              {!hasSelectedKb && <p className="muted helper-text">请先选择至少一个知识库</p>}
            </div>
            <button className={`primary-action ${loading ? 'is-loading' : ''}`} onClick={ask} disabled={loading || !hasQuestion || !hasSelectedKb}>
              {loading ? '生成中...' : '提问'}
            </button>
          </div>
        </div>

        {error && <div className="chat-error-state" role="alert">{error}</div>}
        {loading && <div className="chat-loading-state" role="status">正在检索知识库并生成答案...</div>}

        {result && (
          <div className="answer-card">
            <div className="answer-header">
              <div>
                <span className="eyebrow">步骤 3</span>
                <h3>答案</h3>
              </div>
              <div className="metrics compact-metrics">
                <span>耗时：{result.latency}s</span>
                <span>重试：{result.retry_count}</span>
                <span>资料充分：{result.is_enough ? '是' : '否'}</span>
              </div>
            </div>
            <div className="answer-text chat-answer-text">{result.answer}</div>
            {result.rewritten_question && <p className="muted">改写问题：{result.rewritten_question}</p>}
            {result.evaluation_reason && <p className="muted">评估原因：{result.evaluation_reason}</p>}

            <div className="source-section">
              <h3>引用来源</h3>
              {sources.length === 0 && <div className="chat-empty-state">本次回答未返回引用来源。</div>}
              <div className="source-list">
                {sources.map((source, index) => (
                  <article className="source-card" key={`${source.metadata.source}-${index}`}>
                    <div className="source-card-header">
                      <strong>{source.metadata.kb_name || 'N/A'} / {source.metadata.source || 'N/A'}</strong>
                      <span>页码：{source.metadata.page || 'N/A'} · 片段：{source.metadata.chunk_id || 'N/A'}</span>
                    </div>
                    <p>{source.content}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>
        )}
      </section>
    </section>
  )
}


