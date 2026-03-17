"use client"

import React, { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import { AppSidebar } from "@/components/app-sidebar"
import { AppHeader } from "@/components/app-header"
import { OnboardingWizard } from "@/components/onboarding-wizard"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, token, isAuthenticated, isFirstLogin, updateUserPreferences } = useAuth()
    const router = useRouter()
    const [isClient, setIsClient] = useState(false)

    useEffect(() => {
        setIsClient(true)
    }, [])

    useEffect(() => {
        if (isClient && !isAuthenticated) {
            router.replace("/login")
        }
    }, [isAuthenticated, isClient, router])

    const handleOnboardingComplete = async (data: { syllabus: string; level: string }) => {
        if (!user || !token) return;

        const updatedUser = { ...user, ...data };

        try {
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token}` // FIXED: Token is now sent
                },
                body: JSON.stringify(updatedUser),
            });

            if (!response.ok) throw new Error("Failed to save profile.");

            updateUserPreferences(data);
            console.log("Onboarding complete, preferences saved:", data);

        } catch (error) {
            console.error("Error saving profile:", error);
        }
    }

    if (!isClient || !isAuthenticated) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <LoadingSpinner size="lg" />
            </div>
        )
    }

    return (
        <>
            <div className="flex h-screen bg-background">
                <AppSidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                    <AppHeader />
                    <main className="flex-1 overflow-y-auto p-6">{children}</main>
                </div>
            </div>

            <OnboardingWizard
                isOpen={isFirstLogin}
                onComplete={handleOnboardingComplete}
                userName={user?.name || "User"}
            />
        </>
    )
}