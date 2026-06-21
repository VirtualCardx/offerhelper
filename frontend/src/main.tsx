import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { ConfigProvider, theme } from 'antd'

import App from './App'
import 'antd/dist/reset.css'
import './index.css'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: '#22d3ee',
          colorInfo: '#22d3ee',
          colorBgBase: '#09090b',
          colorTextBase: '#f4f4f5',
          fontFamily: '"IBM Plex Sans", "Noto Sans SC", sans-serif',
          borderRadius: 18,
        },
      }}
    >
      <App />
    </ConfigProvider>
  </StrictMode>,
)
