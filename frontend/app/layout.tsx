import type React from "react"
import type { Metadata } from "next"
import { GeistSans } from "geist/font/sans"
import { Analytics } from "@vercel/analytics/next"
import { Suspense } from "react"
import { AuthProvider } from "@/contexts/AuthContext" // NEW IMPORT
import "./globals.css"

export const metadata: Metadata = {
  title: "Learnix - AI-Powered Exam Preparation",
  description:
      "Master your exams with AI intelligence. Personalized study plans, smart questions, and 24/7 AI tutoring.",
}

export default function RootLayout({
                                     children,
                                   }: Readonly<{
  children: React.ReactNode
}>) {
  return (
      <html lang="en">
      <body className={`font-sans ${GeistSans.variable}`}>
      <Suspense fallback={null}>
        <AuthProvider> {/* NEW WRAPPER */}
          {children}
        </AuthProvider>
      </Suspense>
      <Analytics />
      </body>
      </html>
  )
}