import type React from "react"
import { AppSidebar } from "@/components/app-sidebar"

export default function ExplorerLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  )
}
