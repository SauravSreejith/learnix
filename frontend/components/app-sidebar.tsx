"use client"

import { Brain, BarChart3, Search, Target, MessageCircle, User, HelpCircle, Settings } from "lucide-react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: BarChart3 },
  { name: "Question Explorer", href: "/explorer", icon: Search },
  { name: "Study Planner", href: "/planner", icon: Target },
  { name: "AI Tutor", href: "/tutor", icon: MessageCircle },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <div className="flex h-full w-64 flex-col bg-sidebar border-r border-sidebar-border">
      {/* Logo */}
      <div className="flex items-center space-x-3 px-6 py-4 border-b border-sidebar-border">
        <div className="w-8 h-8 bg-sidebar-primary rounded-lg flex items-center justify-center transition-transform hover:scale-110 duration-200">
          <Brain className="w-5 h-5 text-sidebar-primary-foreground" />
        </div>
        <span className="text-xl font-bold text-sidebar-foreground">Learnix</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-4 py-6 space-y-2">
        {navigation.map((item) => {
          const isActive = pathname === item.href
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
                  : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
              )}
            >
              <item.icon className="w-5 h-5 transition-transform duration-200" />
              <span>{item.name}</span>
            </Link>
          )
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-sidebar-border space-y-2">
        <Link
          href="/profile"
          className={cn(
            "flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 hover:scale-105",
            pathname === "/profile"
              ? "bg-sidebar-accent text-sidebar-accent-foreground shadow-sm"
              : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
          )}
        >
          <User className="w-5 h-5 transition-transform duration-200" />
          <span>Profile</span>
        </Link>
        <Link
          href="/help"
          className="flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground transition-all duration-200 hover:scale-105"
        >
          <HelpCircle className="w-5 h-5 transition-transform duration-200" />
          <span>Help</span>
        </Link>
        <Link
          href="/settings"
          className="flex items-center space-x-3 px-3 py-2 rounded-lg text-sm font-medium text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground transition-all duration-200 hover:scale-105"
        >
          <Settings className="w-5 h-5 transition-transform duration-200" />
          <span>Settings</span>
        </Link>
      </div>
    </div>
  )
}
