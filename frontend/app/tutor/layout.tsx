import type React from "react"
import { AppSidebar } from "@/components/app-sidebar"

export default function TutorLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex h-screen bg-background">
      <AppSidebar />
      <main className="flex-1 overflow-hidden p-6">{children}</main>
    </div>
  )
}
