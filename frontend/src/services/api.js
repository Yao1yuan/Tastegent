import axios from 'axios'

const API_URL = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_URL,
})

export const getMenu = async () => {
  const response = await api.get('/menu')
  return response.data
}

export const chat = async (messages, storeId) => {
  const response = await api.post('/chat', {
    messages,
    store_id: storeId
  })
  return response.data
}

export const uploadFile = async (file) => {
  const formData = new FormData()
  formData.append('file', file)

  const response = await api.post('/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })
  return response.data
}

export default api
