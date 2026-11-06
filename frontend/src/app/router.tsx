import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../components/layout/AppShell'
import { SystemStatusPage } from '../pages/system-status/SystemStatusPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/system-status" replace />} />
          <Route path="/system-status" element={<SystemStatusPage />} />
          <Route path="*" element={<Navigate to="/system-status" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
