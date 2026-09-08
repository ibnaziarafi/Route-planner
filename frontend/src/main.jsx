import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import PDPPage from './components/PDPPage.jsx'
import RealMapPage from './components/RealMapPage.jsx'
import RealMapPDPPage from './components/RealMapPDPPage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {window.location.pathname === '/pdp' ? <PDPPage /> : window.location.pathname === '/real-map-pdp' ? <RealMapPDPPage /> : window.location.pathname === '/real-map' ? <RealMapPage /> : <App />}
  </StrictMode>,
)
