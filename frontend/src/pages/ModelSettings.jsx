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
      <section className="model-page">
        <div className="model-page-header">
          <div>
            <span className="eyebrow">模型服务</span>
            <h2>无权限访问</h2>
            <p className="muted">当前账号无权限访问模型配置。</p>
          </div>
        </div>
        <div className="chat-error-state" role="alert">当前账号无权限访问模型配置</div>
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
      <section className="model-page">
        <div className="model-page-header">
          <div>
            <span className="eyebrow">模型服务</span>
            <h2>模型设置</h2>
            <p className="muted">配置大模型与向量模型服务，用于知识库问答、检索增强和文本嵌入。</p>
          </div>
        </div>
        <div className="chat-loading-state" role="status">{loading ? '模型配置加载中...' : '暂无模型配置'}</div>
        {error && <div className="chat-error-state" role="alert">{error}</div>}
      </section>
    )
  }

  return (
    <section className="model-page">
      <div className="model-page-header">
        <div>
          <span className="eyebrow">模型服务</span>
          <h2>模型设置</h2>
          <p className="muted">配置大模型与向量模型服务，用于知识库问答、检索增强和文本嵌入。</p>
        </div>
        <button className="secondary-action" onClick={loadConfig}>刷新</button>
      </div>

      <div className="model-notice-card">
        <strong>保存后生效</strong>
        <p>LLM 用于答案生成，切换 LLM 通常不需要重建知识库。Embedding 用于文本向量化和检索，如果切换 Embedding 模型，已有知识库通常需要重新构建。</p>
      </div>

      {message && <div className="success model-feedback">{message}</div>}
      {error && <div className="chat-error-state model-feedback" role="alert">{error}</div>}

      <div className="model-settings-grid">
        <section className="model-config-card">
          <div className="model-card-heading">
            <h3>LLM 配置</h3>
            <p className="muted">配置用于生成答案的大模型服务。</p>
          </div>
          <label className="model-field">
            <span>Provider</span>
            <input value={form.llm.provider} onChange={(event) => updateLlm('provider', event.target.value)} />
          </label>
          <label className="model-field">
            <span>Base URL</span>
            <input value={form.llm.base_url} onChange={(event) => updateLlm('base_url', event.target.value)} />
          </label>
          <label className="model-field">
            <span>模型名称</span>
            <input value={form.llm.model} onChange={(event) => updateLlm('model', event.target.value)} />
          </label>
          <label className="model-field">
            <span>Temperature</span>
            <input type="number" step="0.1" value={form.llm.temperature} onChange={(event) => updateLlm('temperature', event.target.value)} />
          </label>
          <label className="model-field">
            <span>API Key</span>
            <input type="password" value={apiKey} placeholder={config.llm.api_key_configured ? '已配置，留空则不修改' : '未配置'} onChange={(event) => setApiKey(event.target.value)} />
            <small>当前状态：{config.llm.api_key_configured ? '已配置' : '未配置'}</small>
          </label>
        </section>

        <section className="model-config-card">
          <div className="model-card-heading">
            <h3>Embedding 配置</h3>
            <p className="muted">配置用于文本向量化和知识库检索的模型。</p>
          </div>
          <label className="model-field">
            <span>Provider</span>
            <input value={form.embedding.provider} onChange={(event) => updateEmbedding('provider', event.target.value)} />
          </label>
          <label className="model-field">
            <span>模型名称</span>
            <input value={form.embedding.model} onChange={(event) => updateEmbedding('model', event.target.value)} />
          </label>
          <label className="model-field">
            <span>Device</span>
            <input value={form.embedding.device} onChange={(event) => updateEmbedding('device', event.target.value)} />
          </label>
        </section>
      </div>

      <div className="model-actions">
        <button className="primary-action" onClick={save}>保存模型配置</button>
      </div>
    </section>
  )
}
