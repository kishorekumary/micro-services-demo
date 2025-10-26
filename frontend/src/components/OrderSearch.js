import React, { useState } from 'react';
import axios from 'axios';
import './OrderSearch.css';

const OrderSearch = () => {
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!searchQuery.trim()) {
      setError('Please enter a search query');
      return;
    }

    setLoading(true);
    setError('');
    
    try {
      const response = await axios.get(`/search?q=${encodeURIComponent(searchQuery)}`);
      setSearchResults(response.data.results || []);
      
      if (response.data.results.length === 0) {
        setError('No orders found matching your search criteria');
      }
    } catch (err) {
      setError('Failed to search orders. Please try again.');
      console.error('Search error:', err);
    } finally {
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setSearchQuery('');
    setSearchResults([]);
    setError('');
  };

  return (
    <div className="order-search">
      <h2>🔍 Search Orders</h2>
      <p className="search-description">
        Search by item name or order ID to find orders in Elasticsearch
      </p>
      
      <form onSubmit={handleSearch} className="search-form">
        <div className="search-input-group">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter item name or order ID..."
            className="search-input"
          />
          <button type="submit" disabled={loading} className="search-button">
            {loading ? '🔄' : '🔍'} Search
          </button>
        </div>
      </form>

      {searchQuery && (
        <button onClick={clearSearch} className="clear-button">
          Clear Search
        </button>
      )}

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Searching orders...</p>
        </div>
      )}

      {searchResults.length > 0 && (
        <div className="search-results">
          <h3>Search Results ({searchResults.length} found)</h3>
          <div className="results-grid">
            {searchResults.map((order, index) => (
              <div key={order.order_id || index} className="order-card">
                <div className="order-header">
                  <span className="order-id">Order #{order.order_id}</span>
                  <span className="order-price">${order.price?.toFixed(2)}</span>
                </div>
                <div className="order-details">
                  <p><strong>Item:</strong> {order.item}</p>
                  <p><strong>Quantity:</strong> {order.quantity}</p>
                  {order.created_at && (
                    <p><strong>Created:</strong> {new Date(order.created_at).toLocaleDateString()}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderSearch;
