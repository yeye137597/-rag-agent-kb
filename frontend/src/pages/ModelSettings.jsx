import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function ModelSettings({ user }) {
  const [config, setConfig] = useState(null)
  const [form, setForm] = useState(null)
  const [apiKey, setApiKey] = useState('')
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)

  async function loadConfig() {
    if (user.role !== 'admin') return
    setLoading(true)
    setError('')
    try {
      const data = await api.modelConfig()
      setConfig(data)
      setForm(data)
    } catch (err) {
      setError(err.message === 'Admin only' ? '当前账号无权限访问模型配置' : err.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadConfig()
  }, [])

  if (user.role !== 'admin') {
    return (
      <section className="panel">
        <h2>无权限访问</h2>
        <div className="error">当前账号无权限访问模型配置</div>
      </section>
    )
  }

  function updateLlm(key, value) {
    setForm({ ...form, llm: { ...form.llm, [key]: value } })
  }

  function updateEmbedding(key, value) {
    setForm({ ...form, embedding: { ...form.embedding, [key]: value } })
  }

  async function save() {
    setError('')
    setMessage('')
    try {
      const payload = {
        llm: {
          provider: form.llm.provider,
          base_url: form.llm.base_url,
          model: form.llm.model,
          temperature: Number(form.llm.temperature),
          api_key: apiKey || null,
        },
        embedding: {
          provider: form.embedding.provider,
          model: form.embedding.model,
          device: form.embedding.device,
        },
      }
      const data = await api.updateModelConfig(payload)
      setConfig(data)
      setForm(data)
      setApiKey('')
      setMessage('模型配置已保存')
    } catch (err) {
      setError(err.message === 'Admin only' ? '当前账号无权限访问模型配置' : err.message)
    }
  }

  if (loading || !form) {
    return (
      <section className="panel">
        <h2>模型设置</h2>
        <p className="muted">{loading ? '模型配置加载中...' : '暂无模型配置'}</p>
        {error && <div className="error">{error}</div>}
      </section>
    )
  }

  return (
    <section className="panel">
      <div className="section-title">
        <h2>模型设置</h2>
        <button onClick={loadConfig}>刷新</button>
      </div>

      <div className="notice">
        注意：LLM 模型用于答案生成，切换 LLM 一般不需要重建知识库。
        Embedding 模型用于文档向量化和检索；如果切换 Embedding 模型，已有知识库通常需要重新构建，否则可能因为向量空间不一致导致无法检索或检索效果异常。
      </div>

      {message && <div className="success">{message}</div>}
      {error && <div className="error">{error}</div>}

      <div className="settings-grid">
        <section>
          <h3>LLM 配置</h3>
          <label>Provider<input value={form.llm.provider} onChange={(event) => updateLlm('provider', event.target.value)} /></label>
          <label>Base URL<input value={form.llm.base_url} onChange={(event) => updateLlm('base_url', event.target.value)} /></label>
          <label>Model<input value={form.llm.model} onChange={(event) => updateLlm('model', event.target.value)} /></label>
          <label>Temperature<input type="number" step="0.1" value={form.llm.temperature} onChange={(event) => updateLlm('temperature', event.target.value)} /></label>
          <label>API Key<input type="password" value={apiKey} placeholder={config.llm.api_key_configured ? '已配置，留空则不修改' : '未配置'} onChange={(event) => setApiKey(event.target.value)} /></label>
          <p className="muted">API Key：{config.llm.api_key_configured ? '已配置' : '未配置'}</p>
        </section>

        <section>
          <h3>Embedding 配置</h3>
          <label>Provider<input value={form.embedding.provider} onChange={(event) => updateEmbedding('provider', event.target.value)} /></label>
          <label>Model<input value={form.embedding.model} onChange={(event) => updateEmbedding('model', event.target.value)} /></label>
          <label>Device<input value={form.embedding.device} onChange={(event) => updateEmbedding('device', event.target.value)} /></label>
        </section>
      </div>

      <div className="actions">
        <button onClick={save}>保存模型配置</button>
      </div>
    </section>
  )
}
