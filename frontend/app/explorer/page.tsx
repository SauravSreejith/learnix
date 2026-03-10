"use client"

import React, { useState, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Slider } from "@/components/ui/slider"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Checkbox } from "@/components/ui/checkbox"
import { Search, ChevronDown, BarChart3, PieChart, Filter } from "lucide-react"
import { Progress } from "@/components/ui/progress"
import { FadeIn } from "@/components/ui/fade-in"
import { StaggerContainer, StaggerItem } from "@/components/ui/stagger-container"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

interface Question {
  question: string
  marks: number
  module: string
  topic: string
  similarity_score: number;
}

interface SearchResults {
  questions: Question[]
  total_matches: number
  module_distribution: Record<string, number>
  marks_distribution: Record<string, number>
}

export default function ExplorerPage() {
  const { currentSubject } = useAuth()
  const [searchQuery, setSearchQuery] = useState("")
  const [similarityThreshold, setSimilarityThreshold] = useState([0.5])
  const [maxResults, setMaxResults] = useState([20])
  const [searchResults, setSearchResults] = useState<SearchResults | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [availableModules, setAvailableModules] = useState<string[]>([])
  const [selectedModules, setSelectedModules] = useState<string[]>([])

  useEffect(() => {
    if (!currentSubject) return;

    const fetchModules = async () => {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/stats?subject_code=${currentSubject.code}`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        setAvailableModules(data.modules || []);
      } catch (error) {
        console.error("Failed to fetch modules:", error);
        setAvailableModules([]);
      }
    };

    fetchModules();
    setSearchResults(null);
    setSelectedModules([]);
    setSearchQuery("");
  }, [currentSubject]);


  const handleModuleToggle = (module: string) => {
    setSelectedModules((prev) => (prev.includes(module) ? prev.filter((m) => m !== module) : [...prev, module]))
  }

  const handleSearch = async () => {
    if (!searchQuery.trim() || !currentSubject) return

    setIsLoading(true)
    setSearchResults(null)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: searchQuery,
          subject_code: currentSubject.code,
          modules: selectedModules,
          similarity_threshold: similarityThreshold[0],
          top_k: maxResults[0]
        })
      });

      if (!response.ok) throw new Error("Search request failed");

      const data = await response.json();
      setSearchResults(data);
    } catch (error) {
      console.error("Failed to perform search:", error);
    } finally {
      setIsLoading(false);
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") handleSearch();
  }

  if (!currentSubject) {
    return <div className="text-center text-muted-foreground">Please select a subject to use the Question Explorer.</div>
  }

  return (
    <div className="space-y-6">
      <FadeIn>
        <div>
          <h1 className="text-3xl font-bold text-foreground">Question Explorer</h1>
          <p className="text-muted-foreground">Search through {currentSubject.name} exam questions using natural language</p>
        </div>
      </FadeIn>

      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-2">
            <Input placeholder={`Search for ${currentSubject.name} questions...`} value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyPress={handleKeyPress} />
            <Button onClick={handleSearch} disabled={isLoading || !searchQuery.trim()}>
              {isLoading ? <LoadingSpinner size="sm" className="mr-2" /> : <Search className="w-4 h-4 mr-2" />}
              {isLoading ? "Searching..." : "Search"}
            </Button>
          </div>
          {availableModules.length > 0 && (
            <Card className="bg-muted/50">
              <Collapsible>
                <CollapsibleTrigger asChild>
                  <Button variant="ghost" className="w-full justify-between text-sm">Filter by Module ({selectedModules.length} selected)<ChevronDown className="w-4 h-4" /></Button>
                </CollapsibleTrigger>
                <CollapsibleContent className="p-4 pt-0">
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                    {availableModules.map((module) => (
                      <div key={module} className="flex items-center space-x-2">
                        <Checkbox id={module} checked={selectedModules.includes(module)} onCheckedChange={() => handleModuleToggle(module)} />
                        <Label htmlFor={module} className="text-sm font-medium cursor-pointer">{module}</Label>
                      </div>
                    ))}
                  </div>
                </CollapsibleContent>
              </Collapsible>
            </Card>
          )}
        </CardContent>
      </Card>

      {searchResults && (
        <FadeIn delay={0.2}>
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 space-y-4">
              <h2 className="text-xl font-semibold">Found {searchResults.total_matches} matching questions</h2>
              {searchResults.questions.length > 0 ? (
                <StaggerContainer className="space-y-4">
                  {searchResults.questions.map((q, index) => (
                    <StaggerItem key={index}>
                      <Card><CardContent className="pt-6 space-y-3">
                        <div className="flex items-start justify-between gap-4">
                          <p className="text-sm leading-relaxed flex-1">{q.question}</p>
                          <div className="flex flex-col items-end gap-2 shrink-0">
                            <Badge variant="outline">{q.marks} Marks</Badge>
                            <Progress value={q.similarity_score * 100} className="w-20 h-2" />
                            <span className="text-xs text-muted-foreground">{Math.round(q.similarity_score * 100)}% match</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-xs text-muted-foreground">
                          <Badge variant="secondary">{q.module}</Badge>
                          <Badge variant="outline">{q.topic}</Badge>
                        </div>
                      </CardContent></Card>
                    </StaggerItem>
                  ))}
                </StaggerContainer>
              ) : (
                <p className="text-muted-foreground">No questions matched your criteria.</p>
              )}
            </div>
            <div className="space-y-6">
              {/* Analytics Charts would be rendered here */}
            </div>
          </div>
        </FadeIn>
      )}

      {!searchResults && !isLoading && (
        <FadeIn delay={0.4}>
          <Card className="text-center py-12"><CardContent>
            <Search className="w-12 h-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">Explore {currentSubject.name} Questions</h3>
            <p className="text-muted-foreground">Enter a query above to begin your search.</p>
          </CardContent></Card>
        </FadeIn>
      )}
    </div>
  )
}