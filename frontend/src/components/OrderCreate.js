import React, { useState } from 'react';
import axios from 'axios';
import './OrderCreate.css';

const OrderCreate = () => {
  const [formData, setFormData] = useState({
    item: '',
    quantity: '',
    price: ''
  });
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    // Clear messages when user starts typing
    if (success) setSuccess('');
    if (error) setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.item || !formData.quantity || !formData.price) {
      setError('Please fill in all fields');
      return;
    }

    if (parseFloat(formData.quantity) <= 0 || parseFloat(formData.price) <= 0) {
      setError('Quantity and price must be greater than 0');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const formDataToSend = new FormData();
      formDataToSend.append('item', formData.item);
      formDataToSend.append('quantity', parseInt(formData.quantity));
      formDataToSend.append('price', parseFloat(formData.price));

      const response = await axios.post('/create_order', formDataToSend, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      
      setSuccess(`Order #${response.data.order_id} created successfully!`);
      setFormData({ item: '', quantity: '', price: '' });
    } catch (err) {
      setError('Failed to create order. Please try again.');
      console.error('Create order error:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="order-create">
      <h2>📝 Create New Order</h2>
      <p className="create-description">
        Add a new order to the system
      </p>
      
      <form onSubmit={handleSubmit} className="create-form">
        <div className="form-group">
          <label htmlFor="item">Item Name</label>
          <input
            type="text"
            id="item"
            name="item"
            value={formData.item}
            onChange={handleChange}
            placeholder="Enter item name..."
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="quantity">Quantity</label>
          <input
            type="number"
            id="quantity"
            name="quantity"
            value={formData.quantity}
            onChange={handleChange}
            placeholder="Enter quantity..."
            min="1"
            className="form-input"
          />
        </div>

        <div className="form-group">
          <label htmlFor="price">Price ($)</label>
          <input
            type="number"
            id="price"
            name="price"
            value={formData.price}
            onChange={handleChange}
            placeholder="Enter price..."
            min="0.01"
            step="0.01"
            className="form-input"
          />
        </div>

        <button type="submit" disabled={loading} className="create-button">
          {loading ? '⏳ Creating...' : '✅ Create Order'}
        </button>
      </form>

      {success && (
        <div className="success-message">
          🎉 {success}
        </div>
      )}

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};

export default OrderCreate;
