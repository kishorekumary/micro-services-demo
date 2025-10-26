import React from 'react';
import './App.css';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import AuthWrapper from './components/AuthWrapper';
import Header from './components/Header';
import OrderSearch from './components/OrderSearch';
import OrderCreate from './components/OrderCreate';

function AppContent() {
  const { isAuthenticated } = useAuth();

  if (!isAuthenticated) {
    return <AuthWrapper />;
  }

  return (
    <div className="App">
      <Header />
      <div className="container">
        <div className="main-content">
          <div className="section">
            <OrderCreate />
          </div>
          
          <div className="section">
            <OrderSearch />
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
