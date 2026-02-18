import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'
import CustomerPage from './pages/CustomerPage'
import AdminPage from './pages/AdminPage'

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<CustomerPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Routes>
    </Router>
  )
}

export default App
