import { useState } from 'react'
import { Outlet } from 'react-router-dom'

import Header from './Header'
import PageContainer from './PageContainer'
import Sidebar from './Sidebar'

function AppShell() {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)

  function openSidebar() {
    setIsSidebarOpen(true)
  }

  function closeSidebar() {
    setIsSidebarOpen(false)
  }

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar
        isOpen={isSidebarOpen}
        onClose={closeSidebar}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <Header onMenuClick={openSidebar} />

        <PageContainer>
          <Outlet />
        </PageContainer>
      </div>
    </div>
  )
}

export default AppShell