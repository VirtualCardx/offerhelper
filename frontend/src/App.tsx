import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import DataHubPage from '@/pages/DataHubPage'
import GovernancePage from '@/pages/GovernancePage'
import OffersPage from '@/pages/OffersPage'
import TasksPage from '@/pages/TasksPage'
import WorkspacePage from '@/pages/WorkspacePage'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate replace to="/workspace" />} />
        <Route path="/workspace" element={<WorkspacePage />} />
        <Route path="/data-hub" element={<DataHubPage />} />
        <Route path="/offers" element={<OffersPage />} />
        <Route path="/governance" element={<GovernancePage />} />
        <Route path="/tasks" element={<TasksPage />} />
      </Routes>
    </BrowserRouter>
  )
}
