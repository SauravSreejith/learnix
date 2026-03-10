"use client"

import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Checkbox } from "@/components/ui/checkbox"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Target, TrendingUp, Calculator } from "lucide-react"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

interface Topic {
  topic: string;
}

interface StrategyItem {
  topic: string
  avg_marks: number
  cumulative_marks: number
}

interface StrategyResponse {
  summary: string
  strategy: StrategyItem[]
}

interface SimulationResponse {
  pass_probability: number
  average_expected_marks: number
  summary: string
}

export default function PlannerPage() {
  const { currentSubject, user } = useAuth();
  const [studiedTopics, setStudiedTopics] = useState<string[]>([]);
  const [internalMarks, setInternalMarks] = useState("");
  const [availableTopics, setAvailableTopics] = useState<Topic[]>([]);
  const [strategy, setStrategy] = useState<StrategyResponse | null>(null);
  const [simulation, setSimulation] = useState<SimulationResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState("strategy");

  const currentSettings = { maxInternal: 50, label: "Internal Marks (out of 50)" }; // Simplified for KTU

  useEffect(() => {
    if (!currentSubject) return;

    const fetchTopics = async () => {
      setIsLoading(true);
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/topics?subject_code=${currentSubject.code}&min_frequency=1`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        const data = await response.json();
        setAvailableTopics(data.topics || []);
      } catch (error) {
        console.error("Failed to fetch topics:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchTopics();
    setStudiedTopics([]);
    setInternalMarks("");
    setStrategy(null);
    setSimulation(null);
  }, [currentSubject]);

  const handleTopicToggle = (topicName: string) => {
    setStudiedTopics((prev) => (prev.includes(topicName) ? prev.filter((t) => t !== topicName) : [...prev, topicName]))
  }

  const generateStrategy = async () => {
    if (!isFormValid || !currentSubject) return;
    setIsLoading(true);
    setActiveTab("strategy");
    setStrategy(null);
    setSimulation(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/pass-strategy`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subject_code: currentSubject.code,
          studied_topics: studiedTopics,
          internal_marks: Number(internalMarks)
        })
      });
      const data = await response.json();
      setStrategy(data);
    } catch (error) {
      console.error("Failed to generate strategy:", error);
    } finally {
      setIsLoading(false);
    }
  }

  const calculateProbability = async () => {
    if (!isFormValid || !currentSubject) return;
    setIsLoading(true);
    setActiveTab("simulation");
    setStrategy(null);
    setSimulation(null);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/pass-simulation`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          subject_code: currentSubject.code,
          studied_topics: studiedTopics,
          internal_marks: Number(internalMarks)
        })
      });
      const data = await response.json();
      setSimulation(data);
    } catch (error) {
      console.error("Failed to run simulation:", error);
    } finally {
      setIsLoading(false);
    }
  }

  const isFormValid = internalMarks !== "" && Number(internalMarks) >= 0 && Number(internalMarks) <= currentSettings.maxInternal;

  if (!currentSubject) {
    return <div className="text-center text-muted-foreground">Please select a subject to use the Study Planner.</div>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-foreground">{currentSubject.name} Study Planner</h1>
        <p className="text-muted-foreground">Create study strategies and simulate your pass probability</p>
      </div>

      <Card>
        <CardHeader><CardTitle>Create Your Study Profile</CardTitle></CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="internal-marks">{currentSettings.label}</Label>
            <Input id="internal-marks" type="number" placeholder={`Enter marks (0-${currentSettings.maxInternal})`} value={internalMarks} onChange={(e) => setInternalMarks(e.target.value)} />
          </div>
          <div className="space-y-3">
            <Label>Topics You've Already Studied</Label>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {availableTopics.map((topic) => (
                <div key={topic.topic} className="flex items-center space-x-2">
                  <Checkbox id={topic.topic} checked={studiedTopics.includes(topic.topic)} onCheckedChange={() => handleTopicToggle(topic.topic)} />
                  <Label htmlFor={topic.topic} className="text-sm font-normal cursor-pointer">{topic.topic}</Label>
                </div>
              ))}
            </div>
          </div>
          <div className="flex flex-col sm:flex-row gap-3">
            <Button onClick={generateStrategy} disabled={!isFormValid || isLoading}><TrendingUp className="w-4 h-4 mr-2" />Generate Pass Strategy</Button>
            <Button variant="outline" onClick={calculateProbability} disabled={!isFormValid || isLoading} className="bg-transparent"><Calculator className="w-4 h-4 mr-2" />Calculate Pass Probability</Button>
          </div>
        </CardContent>
      </Card>

      {isLoading && <div className="flex justify-center py-8"><LoadingSpinner /></div>}

      {(strategy || simulation) && !isLoading && (
        <Card>
          <CardHeader><CardTitle>Your Personalized Results</CardTitle></CardHeader>
          <CardContent>
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="strategy" disabled={!strategy}>Pass Strategy</TabsTrigger>
                <TabsTrigger value="simulation" disabled={!simulation}>Pass Simulation</TabsTrigger>
              </TabsList>
              <TabsContent value="strategy" className="space-y-4 pt-4">
                {strategy && (<>
                  <div className="bg-muted/50 p-4 rounded-lg"><h3 className="font-semibold">Recommended Study Plan</h3><p className="text-sm text-muted-foreground">{strategy.summary}</p></div>
                  <Table><TableHeader><TableRow><TableHead>Topic</TableHead><TableHead className="text-right">Potential Marks</TableHead><TableHead className="text-right">Cumulative Marks</TableHead></TableRow></TableHeader>
                    <TableBody>{strategy.strategy.map((item, index) => (<TableRow key={index}><TableCell>{item.topic}</TableCell><TableCell className="text-right">{item.avg_marks}</TableCell><TableCell className="text-right">{item.cumulative_marks}</TableCell></TableRow>))}</TableBody>
                  </Table>
                </>)}
              </TabsContent>
              <TabsContent value="simulation" className="space-y-4 pt-4">
                {simulation && (<>
                  <div className="bg-muted/50 p-4 rounded-lg"><h3 className="font-semibold">Analysis</h3><p className="text-sm text-muted-foreground">{simulation.summary}</p></div>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <Card className="text-center"><CardHeader><CardTitle>Pass Probability</CardTitle></CardHeader><CardContent><span className="text-4xl font-bold text-primary">{Math.round((simulation.pass_probability || 0) * 100)}%</span></CardContent></Card>
                    <Card className="text-center"><CardHeader><CardTitle>Expected Score</CardTitle></CardHeader><CardContent><span className="text-4xl font-bold text-primary">{simulation.average_expected_marks || 0}</span></CardContent></Card>
                  </div>
                </>)}
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      )}
    </div>
  )
}