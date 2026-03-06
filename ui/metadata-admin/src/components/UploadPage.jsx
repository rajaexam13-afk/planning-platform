import { useState } from 'react'

import { uploadDimensionCsv } from '../api'

export default function UploadPage() {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleUpload = async () => {
    if (!file) {
      setError('Please choose a CSV file first.')
      return
    }

    setLoading(true)
    setError('')

    try {
      const response = await uploadDimensionCsv(file)
      setResult(response.data)
    } catch (uploadError) {
      const message =
        uploadError?.response?.data?.detail || uploadError.message || 'Upload failed.'
      setError(message)
      setResult(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="upload-page">
      <div className="upload-card">
        <h1>Metadata Upload Test</h1>

        <label className="file-input-label" htmlFor="csv-input">
          Choose CSV File
        </label>
        <input
          id="csv-input"
          type="file"
          accept=".csv"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />

        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Uploading...' : 'Upload'}
        </button>

        {error && <p className="error-text">{error}</p>}

        <section className="result-panel">
          <h2>Result:</h2>
          <pre>{JSON.stringify(result ?? {}, null, 2)}</pre>
        </section>
      </div>
    </main>
  )
}
