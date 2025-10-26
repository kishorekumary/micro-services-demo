# Order Search Frontend

A React-based frontend microservice for the Order Management System that provides a modern UI for searching orders from Elasticsearch and creating new orders.

## Features

- **Order Search**: Search orders by item name or order ID using Elasticsearch
- **Order Creation**: Create new orders with item, quantity, and price
- **Real-time Results**: Live search results with modern UI
- **Responsive Design**: Mobile-friendly interface
- **Error Handling**: Comprehensive error handling and user feedback

## Technology Stack

- **React 18**: Modern React with hooks
- **Axios**: HTTP client for API calls
- **CSS3**: Modern styling with gradients and animations
- **Nginx**: Production web server
- **Docker**: Containerized deployment

## Getting Started

### Development Mode

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm start
```

The app will be available at `http://localhost:3000`

### Production Mode

Build and run with Docker:

```bash
docker build -t order-frontend .
docker run -p 3000:80 order-frontend
```

## API Integration

The frontend communicates with the FastAPI backend through the following endpoints:

- `GET /search?q={query}` - Search orders in Elasticsearch
- `POST /create_order` - Create a new order

## Project Structure

```
frontend/
├── public/
│   └── index.html          # HTML template
├── src/
│   ├── components/
│   │   ├── OrderSearch.js  # Search functionality
│   │   ├── OrderSearch.css # Search styling
│   │   ├── OrderCreate.js  # Order creation
│   │   └── OrderCreate.css # Create styling
│   ├── App.js              # Main application
│   ├── App.css             # App styling
│   ├── index.js            # React entry point
│   └── index.css           # Global styles
├── Dockerfile              # Docker configuration
├── nginx.conf              # Nginx configuration
└── package.json            # Dependencies
```

## Environment Variables

The frontend uses a proxy configuration to communicate with the backend. In production, Nginx handles the routing to the backend service.

## Docker Configuration

The frontend uses a multi-stage Docker build:

1. **Build Stage**: Uses Node.js to build the React application
2. **Production Stage**: Uses Nginx to serve the built files

The Nginx configuration includes:
- Static file serving
- API proxy to backend
- React Router support
- Caching headers for static assets
