"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { BookOpen, Target, TrendingUp } from "lucide-react"
import { FadeIn } from "@/components/ui/fade-in"
import { StaggerContainer, StaggerItem } from "@/components/ui/stagger-container"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

interface Stats {
  total_questions: number
  total_exams: number
  total_topics: number
}

interface Topic {
  topic: string
  frequency: number
  total_marks: number
  average_marks: number
}

export default function DashboardPage() {
  const { currentSubject } = useAuth()
  const [stats, setStats] = useState<Stats | null>(null)
  const [topics, setTopics] = useState<Topic[]>([])
  const [minFrequency, setMinFrequency] = useState(2)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // If no subject is selected, do nothing.
    if (!currentSubject) {
      setIsLoading(false);
      setStats(null);
      setTopics([]);
      return;
    };

    const fetchData = async () => {
      setIsLoading(true)
      try {
        // Fetch stats and topics in parallel
        const [statsRes, topicsRes] = await Promise.all([
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/stats?subject_code=${currentSubject.code}`),
          fetch(`${process.env.NEXT_PUBLIC_API_URL}/topics?subject_code=${currentSubject.code}&min_frequency=${minFrequency}`)
        ]);

        if (!statsRes.ok || !topicsRes.ok) {
          throw new Error("Failed to fetch dashboard data");
        }

        const statsData = await statsRes.json();
        const topicsData = await topicsRes.json();

        setStats(statsData);
        setTopics(topicsData.topics || []);

      } catch (error) {
        console.error("Dashboard fetch error:", error)
        // Set to empty state on error
        setStats(null);
        setTopics([]);
      } finally {
        setIsLoading(false)
      }
    }

    fetchData()
  }, [currentSubject, minFrequency])

  // Initial loading or no subject selected state
  if (!currentSubject) {
    return (
        <div className="flex h-full items-center justify-center">
          <Card className="w-full max-w-md text-center">
            <CardHeader>
              <CardTitle>Welcome to your Dashboard</CardTitle>
              <CardDescription>Please select a subject from the header to view its analytics.</CardDescription>
            </CardHeader>
          </Card>
        </div>
    );
  }

  if (isLoading) {
    return <div className="flex justify-center items-center h-full"><LoadingSpinner size="lg" /></div>
  }

  return (
      <div className="space-y-6">
        <FadeIn>
          <div>
            <h1 className="text-3xl font-bold text-foreground">{currentSubject.name} Analytics</h1>
            <p className="text-muted-foreground">Overview of {currentSubject.code} exam preparation data</p>
          </div>
        </FadeIn>

        <StaggerContainer className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <StaggerItem>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Total Questions</CardTitle>
                <BookOpen className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">{stats?.total_questions.toLocaleString() ?? 'N/A'}</div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Exams Analyzed</CardTitle>
                <Target className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">{stats?.total_exams ?? 'N/A'}</div>
              </CardContent>
            </Card>
          </StaggerItem>
          <StaggerItem>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Unique Topics</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold text-primary">{stats?.total_topics ?? 'N/A'}</div>
              </CardContent>
            </Card>
          </StaggerItem>
        </StaggerContainer>

        <FadeIn delay={0.3}>
          <Card>
            <CardHeader>
              <CardTitle>Topic Frequency & Importance</CardTitle>
              <CardDescription>Analyze which topics appear most frequently in past exams for {currentSubject.name}</CardDescription>
              <div className="flex items-center space-x-2 pt-2">
                <Label htmlFor="min-frequency">Minimum Frequency</Label>
                <Input id="min-frequency" type="number" value={minFrequency} onChange={(e) => setMinFrequency(Math.max(1, Number(e.target.value)))} className="w-24" />
              </div>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Topic</TableHead>
                    <TableHead className="text-right">Frequency</TableHead>
                    <TableHead className="text-right">Total Marks</TableHead>
                    <TableHead className="text-right">Average Marks</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {topics.length > 0 ? topics.map((topic, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{topic.topic}</TableCell>
                        <TableCell className="text-right">{topic.frequency}</TableCell>
                        <TableCell className="text-right">{topic.total_marks}</TableCell>
                        <TableCell className="text-right">{topic.average_marks}</TableCell>
                      </TableRow>
                  )) : (
                      <TableRow><TableCell colSpan={4} className="text-center text-muted-foreground">No topics found for the selected criteria.</TableCell></TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </FadeIn>
      </div>
  )
}