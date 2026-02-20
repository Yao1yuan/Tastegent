import { useState, useEffect } from 'react';
import api, { getMenu, uploadFile, createMenuItem, updateMenuItem, deleteMenuItem, API_URL } from '../services/api';
import '../App.css';
import ImageUpload from '../components/ImageUpload';
import Modal from '../components/Modal'; // Import the Modal component



const initialItemState = {
  name: '',
  description: '',
  price: '',
  tags: '',
};

function AdminPage() {
  const [menu, setMenu] = useState([]);
  const [error, setError] = useState('');

  // Modal state
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [modalMode, setModalMode] = useState('create'); // 'create' or 'edit'
  const [currentItem, setCurrentItem] = useState(initialItemState);

  const fetchMenu = async () => {
    try {
      const data = await getMenu();
      setMenu(data);
    } catch (error) {
      console.error('Error fetching menu:', error);
      setError('Failed to fetch menu data.');
    }
  };

  useEffect(() => {
    fetchMenu();
  }, []);

  const openModal = (mode, item = null) => {
    setModalMode(mode);
    if (mode === 'edit' && item) {
      setCurrentItem({ ...item, tags: item.tags.join(', ') });
    } else {
      setCurrentItem(initialItemState);
    }
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setCurrentItem(initialItemState);
    setError('');
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setCurrentItem(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const price = parseFloat(currentItem.price);
      if (isNaN(price)) {
        setError("Price must be a valid number.");
        return;
      }
      const tags = currentItem.tags.split(',').map(tag => tag.trim()).filter(Boolean);

      const payload = { ...currentItem, price, tags };

      if (modalMode === 'create') {
        await createMenuItem(payload);
      } else {
        const { id, imageUrl, ...updateData } = payload;
        await updateMenuItem(id, updateData);
      }

      fetchMenu();
      closeModal();
    } catch (error) {
      console.error(`Error ${modalMode === 'create' ? 'creating' : 'updating'} item:`, error);
      setError(`Failed to ${modalMode === 'create' ? 'create' : 'update'} item.`);
    }
  };

  const handleDeleteItem = async (itemId) => {
    if (window.confirm('Are you sure you want to delete this item?')) {
      try {
        await deleteMenuItem(itemId);
        fetchMenu();
      } catch (error) {
        console.error('Error deleting item:', error);
        setError('Failed to delete item.');
      }
    }
  };

  const handleImageUploadForMenuItem = async (file, itemId) => {
    try {
      const { url: imageUrl } = await uploadFile(file);
      await api.put(`/admin/menu/${itemId}/image`, { imageUrl });
      fetchMenu();
    } catch (error) {
      console.error('Error in image upload process:', error);
      alert('An error occurred during the image upload process.');
    }
  };

  return (
    <div className="admin-page container">
      <header className="admin-header">
        <h1>Menu Management</h1>
        <button onClick={() => openModal('create')} className="add-new-btn">Add New Item</button>
      </header>

      {error && <p className="error-message">{error}</p>}

      <div className="menu-grid">
        {menu.map(item => (
          <div key={item.id} className="menu-card">
            <div className="card-image-container">
              {item.imageUrl ? (
                <img src={`${API_URL}${item.imageUrl}`} alt={item.name} className="card-image" />
              ) : (
                <div className="no-image-placeholder">No Image</div>
              )}
               <div className="image-upload-overlay">
                  <ImageUpload onUpload={(file) => handleImageUploadForMenuItem(file, item.id)} />
              </div>
            </div>
            <div className="card-content">
              <div className="menu-header">
                <h3>{item.name}</h3>
                <span className="price">${item.price.toFixed(2)}</span>
              </div>
              <p>{item.description}</p>
              <div className="card-footer">
                 <div className="card-actions">
                    <button onClick={() => openModal('edit', item)} className="action-btn">Edit</button>
                    <button onClick={() => handleDeleteItem(item.id)} className="action-btn delete">Delete</button>
                 </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      <Modal show={isModalOpen} onClose={closeModal} title={modalMode === 'create' ? 'Add New Item' : 'Edit Item'}>
        <form onSubmit={handleSubmit} className="modal-form">
          <input name="name" value={currentItem.name} onChange={handleFormChange} placeholder="Name" required />
          <textarea name="description" value={currentItem.description} onChange={handleFormChange} placeholder="Description" required />
          <input name="price" type="number" step="0.01" value={currentItem.price} onChange={handleFormChange} placeholder="Price" required />
          <input name="tags" value={currentItem.tags} onChange={handleFormChange} placeholder="Tags (comma-separated)" />
          <div className="modal-actions">
             <button type="button" onClick={closeModal} className="btn-secondary">Cancel</button>
             <button type="submit" className="btn-primary">Save Changes</button>
          </div>
        </form>
        {error && <p className="error-message">{error}</p>}
      </Modal>
    </div>
  );
}

export default AdminPage;
