import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/',
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
