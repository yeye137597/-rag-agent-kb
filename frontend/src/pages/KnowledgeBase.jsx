import React, { useEffect, useState } from 'react'
import { api } from '../api/client'

export default function KnowledgeBase({ user }) {
  const [kbs, setKbs] = useState([])
  const [name, setName] = useState('')
  const [filesByKb, setFilesByKb] = useState({})
  const [kbFiles, setKbFiles] = useState({})
  const [cleanPreview, setCleanPreview] = useState({})
  const [useCleaned, setUseCleaned] = useState({})
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function refresh() {
    setLoading(true)
    setError('')
    try {
      const items = await api.listKbs()
      setKbs(items)
    } catch (err) {
      setError(err.message || '知识库列表加载失败')
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
    setError('')
    setMessage('')
    try {
      const files = filesByKb[kbId]
      if (!files || files.length === 0) {
        setError('请先选择文件')
        return
      }
      const data = await api.uploadFiles(kbId, files)
      setMessage(`已上传 ${data.uploaded_files.length} 个文件`)
      await loadFiles(kbId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function clean(kbId) {
    setError('')
    setMessage('')
    try {
      const data = await api.cleanKbFiles(kbId)
      setCleanPreview({ ...cleanPreview, [kbId]: data.items })
      setMessage(`清洗完成：${data.cleaned_count} 个文件`)
      await loadFiles(kbId)
    } catch (err) {
      setError(err.message)
    }
  }

  async function build(kbId) {
    setError('')
    setMessage('')
    try {
      const data = await api.buildKbWithOptions(kbId, { use_cleaned: !!useCleaned[kbId] })
      setMessage(`构建完成：${data.file_count} 个文件，${data.chunk_count} 个 chunks`)
      if (data.errors?.length) {
        setError(`部分文件解析失败：${data.errors.join('; ')}`)
      }
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  async function deleteKb(kbId) {
    setError('')
    setMessage('')
    if (!window.confirm(`确认删除知识库 ${kbId}？`)) return
    try {
      await api.deleteKb(kbId)
      setMessage('知识库已删除')
      await refresh()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section className="panel">
      <div className="section-title">
        <h2>知识库管理</h2>
        <button onClick={refresh} disabled={loading}>{loading ? '加载中...' : '刷新'}</button>
      </div>
      {user.role === 'admin' && (
        <div className="create-row">
          <input value={name} onChange={(event) => setName(event.target.value)} placeholder="新知识库名称" />
          <button onClick={createKb} disabled={!name.trim()}>创建</button>
        </div>
      )}
      {message && <div className="success">{message}</div>}
      {error && <div className="error">{error}</div>}
      <div className="kb-list">
        {kbs.map((kb) => {
          const files = kbFiles[kb.id]
          const previews = cleanPreview[kb.id] || []
          return (
            <article className="kb-item" key={kb.id}>
              <div>
                <h3>{kb.name}</h3>
                <p className="muted">ID: {kb.id}</p>
                <p>{kb.file_count} files / {kb.chunk_count} chunks</p>
                <p className="muted">更新时间：{kb.updated_at || '-'}</p>
              </div>

              {user.role === 'admin' && (
                <div className="kb-actions">
                  <input
                    type="file"
                    multiple
                    accept=".pdf,.docx,.md,.txt"
                    onChange={(event) => setFilesByKb({ ...filesByKb, [kb.id]: event.target.files })}
                  />
                  <button onClick={() => upload(kb.id)}>上传</button>
                  <button onClick={() => loadFiles(kb.id)}>文件</button>
                  <button onClick={() => clean(kb.id)}>清洗</button>
                  <label className="inline-check">
                    <input
                      type="checkbox"
                      checked={!!useCleaned[kb.id]}
                      onChange={(event) => setUseCleaned({ ...useCleaned, [kb.id]: event.target.checked })}
                    />
                    使用清洗后文件
                  </label>
                  <button onClick={() => build(kb.id)}>构建</button>
                  <button className="danger" onClick={() => deleteKb(kb.id)}>删除</button>
                </div>
              )}

              {files && (
                <div className="file-list">
                  <h4>上传文件</h4>
                  {files.uploads.length === 0 && <p className="muted">暂无上传文件</p>}
                  {files.uploads.map((file) => (
                    <p key={file.filename}>{file.filename} / {Math.round(file.size / 1024)} KB</p>
                  ))}
                  <h4>清洗后文件</h4>
                  {files.processed.length === 0 && <p className="muted">暂无清洗后文件</p>}
                  {files.processed.map((file) => (
                    <p key={file.filename}>{file.filename} / {Math.round(file.size / 1024)} KB</p>
                  ))}
                </div>
              )}

              {previews.length > 0 && (
                <div className="clean-preview">
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
