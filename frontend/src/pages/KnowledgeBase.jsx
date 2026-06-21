import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function KnowledgeBase({ user }) {
  const [kbs, setKbs] = useState([])
  const [name, setName] = useState('')
  const [filesByKb, setFilesByKb] = useState({})
  const [kbFiles, setKbFiles] = useState({})
  const [cleanPreview, setCleanPreview] = useState({})
  const [useCleaned, setUseCleaned] = useState({})
  const [operationLoading, setOperationLoading] = useState({})
  const [operationFeedback, setOperationFeedback] = useState({})
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  function setKbOperation(kbId, operation) {
    setOperationLoading((current) => ({ ...current, [kbId]: operation }))
  }

  function clearKbOperation(kbId) {
    setOperationLoading((current) => ({ ...current, [kbId]: null }))
  }

  function setKbFeedback(kbId, type, text) {
    setOperationFeedback((current) => ({ ...current, [kbId]: { type, text } }))
  }

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      const items = await api.listKbs()
      setKbs(items)
    } catch (err) {
      setError(err.message || '知识库列表加载失败，请稍后重试。')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function loadFiles(kbId) {
    setError('')
    try {
      const data = await api.listKbFiles(kbId)
      setKbFiles({ ...kbFiles, [kbId]: data })
    } catch (err) {
      setError(err.message)
    }
  }

  async function createKb() {
    setError('')
    setMessage('')
    try {
      await api.createKb(name)
      setName('')
      setMessage('知识库已创建')
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function upload(kbId) {
    if (operationLoading[kbId]) return
    setError('')
    setMessage('')
    setKbFeedback(kbId, 'loading', '正在上传文件，请稍候...')
    setKbOperation(kbId, 'upload')
    try {
      const files = filesByKb[kbId]
      if (!files || files.length === 0) {
        setKbFeedback(kbId, 'error', '请先选择文件')
        return
      }
      const data = await api.uploadFiles(kbId, files)
      setMessage(`已上传 ${data.uploaded_files.length} 个文件`)
      setKbFeedback(kbId, 'success', `已上传 ${data.uploaded_files.length} 个文件`)
      await loadFiles(kbId)
    } catch (err) {
      setKbFeedback(kbId, 'error', err.message || '上传失败，请稍后重试。')
      setError(err.message)
    } finally {
      clearKbOperation(kbId)
    }
  }

  async function clean(kbId) {
    if (operationLoading[kbId]) return
    setError('')
    setMessage('')
    setKbFeedback(kbId, 'loading', '正在清洗文档内容，可能需要一些时间...')
    setKbOperation(kbId, 'clean')
    try {
      const data = await api.cleanKbFiles(kbId)
      setCleanPreview({ ...cleanPreview, [kbId]: data.items })
      setMessage(`清洗完成：${data.cleaned_count} 个文件`)
      setKbFeedback(kbId, 'success', `清洗完成：${data.cleaned_count} 个文件`)
      await loadFiles(kbId)
    } catch (err) {
      setKbFeedback(kbId, 'error', err.message || '清洗失败，请稍后重试。')
      setError(err.message)
    } finally {
      clearKbOperation(kbId)
    }
  }

  async function build(kbId) {
    if (operationLoading[kbId]) return
    setError('')
    setMessage('')
    setKbFeedback(kbId, 'loading', '正在构建向量索引，文档较大时可能需要几分钟，请不要重复点击或刷新页面。')
    setKbOperation(kbId, 'build')
    try {
      const data = await api.buildKbWithOptions(kbId, { use_cleaned: !!useCleaned[kbId] })
      setMessage(`构建完成：${data.file_count} 个文件，${data.chunk_count} 个片段`)
      if (data.errors?.length) {
        const errorText = `部分文件解析失败：${data.errors.join('; ')}`
        setKbFeedback(kbId, 'error', errorText)
        setError(errorText)
      } else {
        setKbFeedback(kbId, 'success', `构建完成：${data.file_count} 个文件，${data.chunk_count} 个片段`)
      }
      await refresh()
    } catch (err) {
      setKbFeedback(kbId, 'error', err.message || '构建失败，请稍后重试。')
      setError(err.message)
    } finally {
      clearKbOperation(kbId)
    }
  }

  async function deleteKb(kbId) {
    if (operationLoading[kbId]) return
    setError('')
    setMessage('')
    if (!window.confirm(`确认删除知识库 ${kbId}？`)) return
    setKbFeedback(kbId, 'loading', '正在删除知识库，请稍候...')
    setKbOperation(kbId, 'delete')
    try {
      await api.deleteKb(kbId)
      setMessage('知识库已删除')
      setKbFeedback(kbId, 'success', '知识库已删除')
      await refresh()
    } catch (err) {
      setKbFeedback(kbId, 'error', err.message || '删除失败，请稍后重试。')
      setError(err.message)
    } finally {
      clearKbOperation(kbId)
    }
  }

  return (
    <section className="kb-page">
      <div className="kb-page-header">
        <div>
          <span className="eyebrow">资料管理</span>
          <h2>知识库管理</h2>
          <p className="muted">创建知识库、上传资料，并构建可检索的向量索引。</p>
        </div>
        <button className="secondary-action" onClick={refresh} disabled={loading}>
          {loading ? '加载中...' : '刷新'}
        </button>
      </div>

      {user.role === 'admin' && (
        <div className="kb-create-card">
          <div>
            <h3>创建知识库</h3>
            <p className="muted">为一组资料创建独立的检索空间。</p>
          </div>
          <div className="kb-create-form">
            <input value={name} onChange={(event) => setName(event.target.value)} placeholder="新知识库名称" />
            <button className="primary-action" onClick={createKb} disabled={!name.trim()}>创建</button>
          </div>
        </div>
      )}

      {message && <div className="success kb-feedback">{message}</div>}
      {error && <div className="chat-error-state kb-feedback" role="alert">{error}</div>}
      {loading && <div className="chat-loading-state kb-feedback" role="status">知识库加载中...</div>}
      {!loading && kbs.length === 0 && (
        <div className="chat-empty-state kb-feedback">暂无知识库。请先创建知识库并上传资料。</div>
      )}

      <div className="kb-card-list">
        {kbs.map((kb) => {
          const files = kbFiles[kb.id]
          const previews = cleanPreview[kb.id] || []
          const activeOperation = operationLoading[kb.id]
          const feedback = operationFeedback[kb.id]
          return (
            <article className="kb-manage-card" key={kb.id}>
              <div className="kb-card-header">
                <div>
                  <h3>{kb.name}</h3>
                  <p className="muted">ID：{kb.id}</p>
                </div>
                <div className="kb-stat-row">
                  <span>{kb.file_count} 个文件</span>
                  <span>{kb.chunk_count} 个片段</span>
                </div>
              </div>
              <p className="muted kb-updated-at">更新时间：{kb.updated_at || '-'}</p>

              {feedback && (
                <div className={`kb-operation-status ${feedback.type === 'loading' ? 'is-loading' : ''} ${feedback.type === 'success' ? 'is-success' : ''} ${feedback.type === 'error' ? 'is-error' : ''}`} role={feedback.type === 'error' ? 'alert' : 'status'}>
                  {feedback.text}
                </div>
              )}

              {user.role === 'admin' && (
                <div className="kb-operation-grid">
                  <section className="kb-operation-section">
                    <div className="kb-operation-heading">
                      <h4>上传文件</h4>
                      <p className="muted">支持 PDF、DOCX、Markdown 和 TXT。</p>
                    </div>
                    <div className="kb-upload-row">
                      <input
                        type="file"
                        multiple
                        accept=".pdf,.docx,.md,.txt"
                        disabled={!!activeOperation}
                        onChange={(event) => setFilesByKb({ ...filesByKb, [kb.id]: event.target.files })}
                      />
                      <button className="primary-action" onClick={() => upload(kb.id)} disabled={!!activeOperation}>
                        {activeOperation === 'upload' ? '上传中...' : '上传'}
                      </button>
                    </div>
                  </section>

                  <section className="kb-operation-section">
                    <div className="kb-operation-heading">
                      <h4>文档处理</h4>
                      <p className="muted">查看文件、清洗文本，并构建向量索引。</p>
                    </div>
                    <div className="kb-process-actions">
                      <button className="secondary-action" onClick={() => loadFiles(kb.id)} disabled={!!activeOperation}>文件列表</button>
                      <button className="secondary-action" onClick={() => clean(kb.id)} disabled={!!activeOperation}>
                        {activeOperation === 'clean' ? '清洗中...' : '清洗'}
                      </button>
                      <label className="cleaned-toggle">
                        <input
                          type="checkbox"
                          checked={!!useCleaned[kb.id]}
                          disabled={!!activeOperation}
                          onChange={(event) => setUseCleaned({ ...useCleaned, [kb.id]: event.target.checked })}
                        />
                        <span>
                          <strong>使用清洗后文件</strong>
                          <small>构建索引时优先使用清洗后的文本。</small>
                        </span>
                      </label>
                      <button className="primary-action" onClick={() => build(kb.id)} disabled={!!activeOperation}>
                        {activeOperation === 'build' ? '构建中...' : '构建'}
                      </button>
                    </div>
                  </section>

                  <section className="kb-danger-zone">
                    <div>
                      <h4>危险操作</h4>
                      <p className="muted">删除后，该知识库及相关索引将不可用。</p>
                    </div>
                    <button className="danger compact-danger" onClick={() => deleteKb(kb.id)} disabled={!!activeOperation}>
                      {activeOperation === 'delete' ? '删除中...' : '删除'}
                    </button>
                  </section>
                </div>
              )}

              {files && (
                <div className="file-list kb-file-panel">
                  <section>
                    <h4>上传文件</h4>
                    {files.uploads.length === 0 && <p className="muted">暂无上传文件</p>}
                    {files.uploads.map((file) => (
                      <p key={file.filename}>{file.filename} / {Math.round(file.size / 1024)} KB</p>
                    ))}
                  </section>
                  <section>
                    <h4>清洗后文件</h4>
                    {files.processed.length === 0 && <p className="muted">暂无清洗后文件</p>}
                    {files.processed.map((file) => (
                      <p key={file.filename}>{file.filename} / {Math.round(file.size / 1024)} KB</p>
                    ))}
                  </section>
                </div>
              )}

              {previews.length > 0 && (
                <div className="clean-preview kb-preview-panel">
                  <h4>清洗预览</h4>
                  {previews.map((item) => (
                    <details key={item.filename} open>
                      <summary>{item.filename}：{item.error || `${item.original_chars} -> ${item.cleaned_chars} 字符`}</summary>
                      {item.error ? (
                        <div className="error">{item.error}</div>
                      ) : (
                        <div className="preview-grid">
                          <textarea value={item.original_preview} disabled rows={8} />
                          <textarea value={item.cleaned_preview} disabled rows={8} />
                        </div>
                      )}
                    </details>
                  ))}
                </div>
              )}
            </article>
          )
        })}
      </div>
    </section>
  )
}
