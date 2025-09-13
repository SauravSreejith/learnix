"use client"

import { useAuth } from "@/contexts/AuthContext"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { User, LogOut } from "lucide-react"
import { useState, useEffect } from "react"

interface Subject {
  code: string;
  name: string;
}

export function AppHeader() {
  const { user, logout, currentSubject, setCurrentSubject } = useAuth()
  const router = useRouter()
  const [subjects, setSubjects] = useState<Subject[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch subjects dynamically based on user profile
  useEffect(() => {
    if (user?.syllabus && user?.level) {
      setIsLoading(true);
      const fetchSubjects = async () => {
        try {
          // CORRECTED LINE: Added the '?' before the query parameters.
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/subjects?syllabus=${user.syllabus}&level=${user.level}`);
          if (!response.ok) throw new Error("Failed to fetch subjects");
          const data = await response.json();
          const fetchedSubjects = data.subjects || [];
          setSubjects(fetchedSubjects);

          // Set the first subject as default if none is selected or the current one is not in the new list
          if (fetchedSubjects.length > 0) {
            const currentSubjectStillValid = fetchedSubjects.some(s => s.code === currentSubject?.code);
            if (!currentSubject || !currentSubjectStillValid) {
              setCurrentSubject(fetchedSubjects[0]);
            }
          } else {
            setCurrentSubject(null); // No subjects available
          }

        } catch (error) {
          console.error(error);
          setSubjects([]);
        } finally {
          setIsLoading(false);
        }
      };
      fetchSubjects();
    } else {
      setIsLoading(false);
      setSubjects([]);
    }
  }, [user?.syllabus, user?.level, setCurrentSubject, currentSubject]);

  const handleSubjectChange = (subjectCode: string) => {
    const subject = subjects.find(s => s.code === subjectCode);
    if (subject) {
      setCurrentSubject(subject);
    }
  }

  const navigateToProfile = () => {
    router.push('/profile');
  };

  return (
      <header className="flex h-16 shrink-0 items-center justify-between border-b bg-background px-6">
        <div>
          <Select onValueChange={handleSubjectChange} value={currentSubject?.code || ""}>
            <SelectTrigger className="w-[280px]">
              <SelectValue placeholder={isLoading ? "Loading subjects..." : "Select a subject..."} />
            </SelectTrigger>
            <SelectContent>
              {subjects.length > 0 ? subjects.map(subject => (
                  <SelectItem key={subject.code} value={subject.code}>
                    {subject.name} ({subject.code})
                  </SelectItem>
              )) : <SelectItem value="none" disabled>No subjects found</SelectItem>}
            </SelectContent>
          </Select>
        </div>
        <div className="flex items-center gap-4">
        <span className="text-sm font-medium text-muted-foreground hidden sm:inline">
          {user?.name}
        </span>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="icon" className="overflow-hidden rounded-full">
                <User className="h-4 w-4" />
                <span className="sr-only">Toggle user menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>{user?.email}</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={navigateToProfile}>Profile</DropdownMenuItem>
              <DropdownMenuItem disabled>Settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>
  )
}