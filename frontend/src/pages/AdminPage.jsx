import { useState, useEffect } from 'react';
import axios from 'axios';
import '../App.css';
import ImageUpload from '../components/ImageUpload'; // Import the component

const API_URL = 'http://localhost:8000';
const ADMIN_PASSWORD = 'supersecret';

function AdminPage() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [password, setPassword] = useState('');
  const [menu, setMenu] = useState([]);
  const [error, setError] = useState('');

  const fetchMenu = () => {
    axios.get(`${API_URL}/menu`)
      .then(response => {
        setMenu(response.data);
      })
      .catch(error => {
        console.error('Error fetching menu:', error);
        setError('Failed to fetch menu data.');
      });
  };

  useEffect(() => {
    if (isAuthenticated) {
      fetchMenu();
    }
  }, [isAuthenticated]);

  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (password === ADMIN_PASSWORD) {
      setIsAuthenticated(true);
      setError('');
    } else {
      setError('Incorrect password');
    }
  };

  // New handler for uploading and associating image with a menu item
  const handleImageUploadForMenuItem = async (file, itemId) => {
    const formData = new FormData();
    formData.append('file', file);

    try {
      // 1. Upload the image
      const uploadResponse = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      const { url: imageUrl } = uploadResponse.data;

      // 2. Associate the image with the menu item
      await axios.put(
        `${API_URL}/admin/menu/${itemId}/image`,
        { imageUrl },
        {
          headers: {
            'X-Admin-Password': ADMIN_PASSWORD,
          },
        }
      );

      // 3. Refresh the menu to show the new image
      fetchMenu();

    } catch (error) {
      console.error('Error in image upload and association process:', error);
      alert('An error occurred. Please check the console and try again.');
    }
  };

  if (!isAuthenticated) {
    return (
      <div className="container" style={{ textAlign: 'center', paddingTop: '50px' }}>
        <h2>Admin Login</h2>
        <form onSubmit={handlePasswordSubmit} style={{ display: 'inline-block' }}>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter admin password"
            style={{ padding: '10px', marginRight: '10px' }}
          />
          <button type="submit" style={{ padding: '10px' }}>Login</button>
        </form>
        {error && <p style={{ color: 'red' }}>{error}</p>}
      </div>
    );
  }

  return (
    <div className="admin-page container">
      <header>
        <h1>Menu Management</h1>
      </header>
      <div className="menu-section">
        <div className="menu-items">
          {menu.map(item => (
            <div key={item.id} className="admin-menu-item menu-item">
              <div className="menu-header">
                <h3>{item.name}</h3>
                <span className="price">${item.price.toFixed(2)}</span>
              </div>
              <p>{item.description}</p>
              <div className="image-section">
                {item.imageUrl ? (
                  <img
                    src={`${API_URL}${item.imageUrl}`}
                    alt={item.name}
                    style={{ width: '150px', height: '150px', objectFit: 'cover', borderRadius: '8px' }}
                  />
                ) : (
                  <div style={{ width: '150px', height: '150px', background: '#f0f0f0', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '8px' }}>
                    <span>No image</span>
                  </div>
                )}
                <div className="upload-placeholder" style={{ marginTop: '10px' }}>
                   {/* Pass a function to onUpload that includes the item's ID */}
                   <ImageUpload onUpload={(file) => handleImageUploadForMenuItem(file, item.id)} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default AdminPage;
