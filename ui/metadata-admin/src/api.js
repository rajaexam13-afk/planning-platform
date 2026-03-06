import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000',
})

export function uploadDimensionCsv(file) {
  const formData = new FormData()
  formData.append('file', file)

  return api.post('/upload/dimension', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
}
