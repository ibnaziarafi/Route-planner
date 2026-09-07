import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import PDPPage from './components/PDPPage.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    {window.location.pathname === '/pdp' ? <PDPPage /> : <App />}
  </StrictMode>,
)
