"use client"

import React, { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/contexts/AuthContext"
import { AppSidebar } from "@/components/app-sidebar"
import { AppHeader } from "@/components/app-header"
import { OnboardingWizard } from "@/components/onboarding-wizard"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
    const { user, isAuthenticated, isFirstLogin, updateUserPreferences } = useAuth()
    const router = useRouter()
    const [isClient, setIsClient] = useState(false)

    // This effect ensures the logic only runs on the client-side
    useEffect(() => {
        setIsClient(true)
    }, [])

    useEffect(() => {
        if (isClient && !isAuthenticated) {
            router.replace("/login")
        }
    }, [isAuthenticated, isClient, router])

    const handleOnboardingComplete = async (data: { syllabus: string; level: string }) => {
        if (!user) return;

        const updatedUser = { ...user, ...data };

        try {
            // API call to save the user's new preferences to the backend
            const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile`, {
                method: "PUT",
                headers: {
                    "Content-Type": "application/json",
                    // In a real app with JWT: "Authorization": `Bearer ${localStorage.getItem("token")}`
                },
                body: JSON.stringify(updatedUser),
            });

            if (!response.ok) throw new Error("Failed to save profile.");

            // If the API call is successful, update the state in the frontend
            updateUserPreferences(data);
            console.log("Onboarding complete, preferences saved:", data);

        } catch (error) {
            console.error("Error saving profile:", error);
            // Optionally show an error toast to the user
        }
    }

    // While waiting for client-side check, show a full-page loader
    if (!isClient || !isAuthenticated) {
        return (
            <div className="flex h-screen items-center justify-center bg-background">
                <LoadingSpinner size="lg" />
            </div>
        )
    }

    // The main layout is now ALWAYS rendered.
    // The wizard will appear on top of it if isFirstLogin is true.
    return (
        <>
            <div className="flex h-screen bg-background">
                <AppSidebar />
                <div className="flex-1 flex flex-col overflow-hidden">
                    <AppHeader />
                    <main className="flex-1 overflow-y-auto p-6">{children}</main>
                </div>
            </div>

            {/* Conditionally render the wizard as an overlay */}
            <OnboardingWizard
                isOpen={isFirstLogin}
                onComplete={handleOnboardingComplete}
                userName={user?.name || "User"}
            />
        </>
    )
}