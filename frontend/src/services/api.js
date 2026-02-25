import axios from 'axios'

// Use VITE_API_URL if set, otherwise default to relative path '' to use Vite proxy (locally)
export const API_URL = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: API_URL,
})

api.interceptors.request.use((config) => {
  // TODO: Storing JWT in localStorage is vulnerable to XSS.
  // In a production environment, this should be moved to an httpOnly cookie.
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const getMenu = async () => {
  const response = await api.get('/menu')
  return response.data
}

export const login = async (username, password) => {
  const params = new URLSearchParams();
  params.append('username', username);
  params.append('password', password);

  const response = await api.post('/token', params, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  return response.data;
};

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

export const createMenuItem = async (itemData) => {
  const response = await api.post('/admin/menu', itemData);
  return response.data;
};

export const updateMenuItem = async (itemId, itemData) => {
  const response = await api.put(`/admin/menu/${itemId}`, itemData);
  return response.data;
};

export const deleteMenuItem = async (itemId) => {
  const response = await api.delete(`/admin/menu/${itemId}`);
  return response.data;
};

export default api
