# Frontend Setup & Development Guide

## 🎨 Modern Web UI for MAS Code Review Pipeline

This document covers the beautiful React-based frontend for the MAS Code Review Pipeline with real-time monitoring and report management.

## Quick Start

### Prerequisites
- Node.js 16+ and npm installed
- Python 3.9+ with the backend running

### Installation

```bash
cd frontend
npm install
```

### Development Mode

Run the frontend in development mode with hot reload:

```bash
npm run dev
```

The app will open at `http://localhost:3000`

> **Note:** This requires the backend to be running on `http://localhost:8000`

### Production Build

Build the frontend for production:

```bash
npm run build
```

This creates an optimized `build/` directory ready for deployment.

### Serve Production Build

```bash
npm run serve
```

## 🏗️ Project Structure

```
frontend/
├── package.json              # Dependencies and scripts
├── public/
│   └── index.html            # HTML template
├── src/
│   ├── index.js              # React entry point
│   ├── App.js                # Main app component
│   ├── App.css               # Global styles
│   ├── index.css             # Base styles
│   └── components/
│       ├── Header.js         # App header with logo
│       ├── Header.css
│       ├── ReviewForm.js     # Form to start reviews
│       ├── ReviewForm.css
│       ├── PipelineMonitor.js # Real-time execution monitoring
│       ├── PipelineMonitor.css
│       ├── ResultsPanel.js   # Results display
│       ├── ResultsPanel.css
│       ├── ReportsHistory.js # Report/log history
│       └── ReportsHistory.css
└── Dockerfile               # Container image

```

## 🎯 Features

### 1. **New Review** Tab
- Enter a directory path to analyze
- Select an Ollama model (optional)
- Quick access to sample code for testing
- Real-time validation and error messages

### 2. **Monitor** Tab
- Real-time pipeline status tracking
- Progress bar with percentage
- Timeline view showing all agents
- Live execution status (Pending, Running, Completed, Error)
- Download results when ready

### 3. **History** Tab
- Browse all generated reports
- View trace logs
- Download past reports and logs
- Organized by creation date

## 🌐 API Integration

The frontend communicates with the FastAPI backend via REST endpoints:

```
GET  /api/health              # Check backend health
POST /api/review              # Start a new review
GET  /api/status/{run_id}     # Get pipeline status
GET  /api/result/{run_id}     # Get pipeline results
GET  /api/reports             # List all reports
GET  /api/report/{filename}   # Download report
GET  /api/logs                # List all trace logs
GET  /api/log/{filename}      # Download trace log
GET  /api/config              # Get pipeline configuration
```

## 🎨 Design System

### Colors
- **Primary**: Cyan (`#38bdf8`)
- **Background**: Slate Blue (`#0f172a`, `#1e293b`)
- **Text**: Slate Gray (`#f1f5f9`, `#cbd5e1`)
- **Success**: Green (`#10b981`)
- **Warning**: Amber (`#f59e0b`)
- **Error**: Red (`#ef4444`)

### Typography
- **Font Family**: System fonts (Apple system, Segoe UI, Roboto, etc.)
- **Font Smoothing**: Antialiased for crisp rendering

### Components
- **Cards**: Semi-transparent with backdrop blur
- **Buttons**: Gradient backgrounds with hover effects
- **Inputs**: Dark background with focus states
- **Animations**: Fade-in, slide-down, and pulse effects

## 🚀 Deployment

### Docker Setup

Build and run with Docker:

```bash
docker build -t mas-code-review-frontend:latest .
docker run -p 3000:3000 -e REACT_APP_API_URL=http://localhost:8000/api mas-code-review-frontend:latest
```

### Docker Compose

The full stack can be deployed using docker-compose:

```bash
docker-compose up
```

This starts:
- **Backend API**: Port 8000
- **Frontend**: Port 3000
- **Ollama Service**: Port 11434

### Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: `http://localhost:8000/api`)

## 🛠️ Development Tips

### Hot Reloading
Changes to component files are automatically reflected in the browser during development.

### Browser DevTools
Open DevTools (F12) to inspect elements and debug JavaScript.

### Network Tab
Monitor API calls in the Network tab to debug backend communication.

### Console Errors
Check the console for any React or JavaScript errors.

## 📱 Responsive Design

The UI is fully responsive:
- **Desktop** (1200px+): Multi-column layouts
- **Tablet** (768px-1199px): Adapted layouts
- **Mobile** (<768px): Single-column, optimized touch targets

## ♿ Accessibility

- Semantic HTML structure
- Proper ARIA labels
- Keyboard navigation support
- High contrast ratios
- Reduced motion preferences respected

## 🐛 Troubleshooting

### Frontend won't connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS settings in `api.py`
- Verify `REACT_APP_API_URL` environment variable

### Styles not loading
- Clear browser cache (Ctrl+Shift+Delete)
- Run `npm install` again
- Check for CSS file loading errors in DevTools

### Build fails
- Delete `node_modules` and `build` directories
- Run `npm install` again
- Check Node.js version (requires 16+)

## 📚 Additional Resources

- [React Documentation](https://react.dev)
- [Axios Documentation](https://axios-http.com)
- [Modern CSS Guide](https://web.dev)

## 🤝 Contributing

To modify the frontend:

1. Create a new branch
2. Make changes to components in `src/components/`
3. Test locally with `npm run dev`
4. Commit and push changes
5. Create a pull request

## 📄 License

Same as the main project (CTSE Assignment 2)
