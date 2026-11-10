import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'

import { AppShell } from '../components/layout/AppShell'
import { AssetVaultPage } from '../pages/assets/AssetVaultPage'
import { QrLoginPage } from '../pages/auth/QrLoginPage'
import { DeviceManagementPage } from '../pages/devices/DeviceManagementPage'
import { NotesPage } from '../pages/notes/NotesPage'
import { SteganographyLabPage } from '../pages/steganography/SteganographyLabPage'
import { SystemStatusPage } from '../pages/system-status/SystemStatusPage'

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/login" replace />} />
          <Route path="/login" element={<QrLoginPage />} />
          <Route path="/auth" element={<Navigate to="/login" replace />} />
          <Route path="/devices" element={<DeviceManagementPage />} />
          <Route path="/notes" element={<NotesPage />} />
          <Route path="/assets" element={<AssetVaultPage />} />
          <Route path="/steganography" element={<SteganographyLabPage />} />
          <Route path="/system-status" element={<SystemStatusPage />} />
          <Route path="*" element={<Navigate to="/login" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}
