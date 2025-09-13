"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { OnboardingWizard } from "@/components/onboarding-wizard"
import { User, Settings, BookOpen, Edit3, Save, X } from "lucide-react"

export default function ProfilePage() {
  const { user, login, token } = useAuth(); // Get user and a way to update it
  const [isEditing, setIsEditing] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize state from the context, providing fallbacks.
  const [editedName, setEditedName] = useState(user?.name || "");

  // Update local state if user context changes
  useEffect(() => {
    if (user) {
      setEditedName(user.name);
    }
  }, [user]);

  const handleProfileUpdate = async (updatedData: any) => {
    setIsLoading(true);
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/profile`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}` // Assuming token-based auth
        },
        body: JSON.stringify(updatedData)
      });
      if (!response.ok) throw new Error("Failed to update profile.");
      const data = await response.json();

      // Update the user in the AuthContext
      login(data.user, token, user?.is_first_login || false);
      // Ideally, show a success toast message here.
      return true;
    } catch (error) {
      console.error(error);
      // Ideally, show an error toast message here.
      return false;
    } finally {
      setIsLoading(false);
    }
  }

  const handleSave = async () => {
    if (editedName === user?.name) {
      setIsEditing(false);
      return;
    }
    const success = await handleProfileUpdate({ ...user, name: editedName });
    if (success) {
      setIsEditing(false);
    }
  }

  const handleCancel = () => {
    setEditedName(user?.name || "");
    setIsEditing(false);
  }

  const handleOnboardingComplete = async (data: { syllabus: string; level: string }) => {
    const success = await handleProfileUpdate({ ...user, syllabus: data.syllabus, level: data.level, is_first_login: false });
    if (success) {
      setShowOnboarding(false);
    }
  }

  const getSyllabusFullName = (syllabus: string) => {
    switch (syllabus) {
      case "KTU":
        return "Kerala Technological University"
      case "CBSE":
        return "Central Board of Secondary Education"
      case "ICSE":
        return "Indian Certificate of Secondary Education"
      default:
        return syllabus
    }
  }

  const getLevelDisplayName = (syllabus: string, level: string) => {
    if (syllabus === "KTU") {
      // Simple validation for level format
      return level.startsWith("S") ? `Semester ${level.substring(1)}` : level;
    } else {
      return `Grade ${level}`
    }
  }

  // Handle case where user is not loaded yet
  if (!user) {
    return <div>Loading profile...</div>;
  }

  return (
      <div className="space-y-6">
        <div className="flex items-center space-x-3">
          <User className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold">Profile</h1>
            <p className="text-muted-foreground">Manage your account settings and preferences</p>
          </div>
        </div>

        <div className="grid gap-6 max-w-2xl">
          {/* User Information Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <User className="h-5 w-5" />
                <span>User Information</span>
              </CardTitle>
              <CardDescription>Your personal account details</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="name">Full Name</Label>
                {isEditing ? (
                    <div className="flex space-x-2">
                      <Input
                          id="name"
                          value={editedName}
                          onChange={(e) => setEditedName(e.target.value)}
                          className="flex-1"
                          disabled={isLoading}
                      />
                      <Button size="sm" onClick={handleSave} className="px-3" disabled={isLoading}>
                        <Save className="h-4 w-4" />
                      </Button>
                      <Button size="sm" variant="outline" onClick={handleCancel} className="px-3 bg-transparent" disabled={isLoading}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                ) : (
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium bg-muted px-3 py-2 rounded-md flex-1">{user.name}</span>
                      <Button size="sm" variant="outline" onClick={() => setIsEditing(true)} className="ml-2">
                        <Edit3 className="h-4 w-4" />
                      </Button>
                    </div>
                )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="text-sm font-medium bg-muted px-3 py-2 rounded-md text-muted-foreground">
                  {user.email}
                </div>
                <p className="text-xs text-muted-foreground">Email cannot be changed from this page</p>
              </div>
            </CardContent>
          </Card>

          {/* Syllabus Settings Card */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BookOpen className="h-5 w-5" />
                <span>Academic Settings</span>
              </CardTitle>
              <CardDescription>Your educational syllabus and current level</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Current Syllabus</Label>
                  <div className="text-sm font-medium bg-primary/5 px-3 py-2 rounded-md border border-primary/20">
                    <div className="font-semibold text-primary">{user.syllabus || "Not Set"}</div>
                    <div className="text-xs text-muted-foreground">{getSyllabusFullName(user.syllabus || "")}</div>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label>Current Level</Label>
                  <div className="text-sm font-medium bg-primary/5 px-3 py-2 rounded-md border border-primary/20">
                    <div className="font-semibold text-primary">{user.level || "Not Set"}</div>
                    <div className="text-xs text-muted-foreground">
                      {getLevelDisplayName(user.syllabus || "", user.level || "")}
                    </div>
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t">
                <Button onClick={() => setShowOnboarding(true)} variant="outline" className="w-full">
                  <Settings className="h-4 w-4 mr-2" />
                  Change Syllabus
                </Button>
                <p className="text-xs text-muted-foreground mt-2 text-center">
                  This will update your syllabus and level preferences across the entire app
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Account Actions */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Settings className="h-5 w-5" />
                <span>Account Actions</span>
              </CardTitle>
              <CardDescription>Manage your account settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="outline" className="w-full justify-start bg-transparent">
                Change Password
              </Button>
              <Button variant="outline" className="w-full justify-start bg-transparent">
                Download My Data
              </Button>
              <Button variant="destructive" className="w-full justify-start">
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Onboarding Wizard Modal */}
        <OnboardingWizard isOpen={showOnboarding} onComplete={handleOnboardingComplete} userName={user.name} />
      </div>
  )
}