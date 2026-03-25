/**
 * Centralized API configuration for Ocean
 * Determines the backend API URL based on environment and deployment
 * 
 * SETUP INSTRUCTIONS:
 * 1. In Vercel dashboard → Settings → Environment Variables
 * 2. Add: VITE_API_BASE_URL = https://YOUR_RAILWAY_BACKEND_URL
 * 3. The URL should NOT include /api (e.g., https://ocean-api.railway.app)
 */

// Get API base URL from environment or auto-detect
export function getApiBase() {
  // 1. Priority: explicit environment variable (set in Vercel)
  if (import.meta.env.VITE_API_BASE_URL) {
    const url = import.meta.env.VITE_API_BASE_URL.replace(/\/+$/, '')
    // Ensure /api is appended if not present
    return url.endsWith('/api') ? url : `${url}/api`
  }
  
  // 2. On Vercel deployed frontend
  if (typeof window !== 'undefined' && location.hostname.endsWith('vercel.app')) {
    console.error('[Ocean API] VITE_API_BASE_URL environment variable not set in Vercel!')
    console.error('[Ocean API] Go to Vercel Settings → Environment Variables and add VITE_API_BASE_URL')
    return '/api' // Fallback (will likely fail)
  }
  
  // 3. Local development: use localhost
  if (typeof window !== 'undefined' && (location.hostname === 'localhost' || location.hostname === '127.0.0.1')) {
    return 'http://localhost:8000/api'
  }
  
  // 4. Default: try relative paths (won't work across domains)
  return '/api'
}

export const API_BASE = getApiBase()

// Log for debugging
if (typeof window !== 'undefined') {
  console.log('[Ocean API] Configured URL:', API_BASE)
}
