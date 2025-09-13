"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge" // <--- ADD THIS LINE
import { Brain, GraduationCap, School, BookOpen, ChevronRight, ChevronLeft, CheckCircle } from "lucide-react"

interface OnboardingWizardProps {
    isOpen: boolean
    onComplete: (data: { syllabus: string; level: string }) => void
    userName: string
}

export function OnboardingWizard({ isOpen, onComplete, userName }: OnboardingWizardProps) {
    const [currentStep, setCurrentStep] = useState(1)
    const [selectedSyllabus, setSelectedSyllabus] = useState("")
    const [selectedLevel, setSelectedLevel] = useState("")

    const syllabusOptions = [
        { id: "KTU", name: "KTU", description: "Kerala Technological University", icon: GraduationCap },
        { id: "CBSE", name: "CBSE", description: "Central Board of Secondary Education", icon: School },
        { id: "ICSE", name: "ICSE", description: "Indian Certificate of Secondary Education", icon: BookOpen },
    ]

    const getLevelOptions = () => {
        if (selectedSyllabus === "KTU") {
            return Array.from({ length: 8 }, (_, i) => ({ value: `S${i + 1}`, label: `Semester ${i + 1}` }))
        } else if (selectedSyllabus === "CBSE" || selectedSyllabus === "ICSE") {
            return [
                { value: "10", label: "10th Grade" },
                { value: "12", label: "12th Grade" },
            ]
        }
        return []
    }

    const handleNext = () => {
        if (currentStep < 4) setCurrentStep(currentStep + 1)
    }

    const handleBack = () => {
        if (currentStep > 1) setCurrentStep(currentStep - 1)
    }

    const handleComplete = () => {
        onComplete({
            syllabus: selectedSyllabus,
            level: selectedLevel,
        })
    }

    const canProceed = () => {
        if (currentStep === 2) return selectedSyllabus !== ""
        if (currentStep === 3) return selectedLevel !== ""
        return true
    }

    // This prevents the dialog from closing when clicking outside of it
    const handleInteractOutside = (event: Event) => {
        event.preventDefault();
    };

    return (
        <Dialog open={isOpen}>
            <DialogContent className="max-w-md" onInteractOutside={handleInteractOutside}>
                <DialogHeader>
                    <div className="flex justify-center mb-4">
                        <div className="p-3 bg-primary/10 rounded-full">
                            <Brain className="h-8 w-8 text-primary" />
                        </div>
                    </div>
                    <DialogTitle className="text-center text-2xl font-bold">
                        {currentStep === 1 && `Welcome, ${userName}!`}
                        {currentStep === 2 && "Choose Your Syllabus"}
                        {currentStep === 3 && "Specify Your Level"}
                        {currentStep === 4 && "All Set!"}
                    </DialogTitle>
                    <DialogDescription className="text-center">
                        {currentStep === 1 && "Let's personalize your Learnix experience."}
                        {currentStep === 2 && "Select your educational board to get tailored content."}
                        {currentStep === 3 && "This helps us find the right materials for you."}
                        {currentStep === 4 && "Your profile is ready. Happy learning!"}
                    </DialogDescription>
                </DialogHeader>

                <div className="pt-4">
                    {/* Progress indicator */}
                    <div className="flex items-center justify-center space-x-2 mb-6">
                        {[1, 2, 3, 4].map((step) => (
                            <div key={step} className={`w-2 h-2 rounded-full transition-colors ${step <= currentStep ? "bg-primary" : "bg-muted"}`} />
                        ))}
                    </div>

                    {currentStep === 1 && <div className="h-32" />}

                    {currentStep === 2 && (
                        <div className="space-y-3">
                            {syllabusOptions.map((option) => {
                                const Icon = option.icon
                                return (
                                    <Card key={option.id} className={`cursor-pointer transition-all hover:border-primary ${selectedSyllabus === option.id ? "border-primary ring-2 ring-primary/20" : ""}`} onClick={() => setSelectedSyllabus(option.id)}>
                                        <CardContent className="flex items-center space-x-4 p-4">
                                            <Icon className="h-6 w-6 text-primary" />
                                            <div>
                                                <h3 className="font-semibold">{option.name}</h3>
                                                <p className="text-sm text-muted-foreground">{option.description}</p>
                                            </div>
                                        </CardContent>
                                    </Card>
                                )
                            })}
                        </div>
                    )}

                    {currentStep === 3 && (
                        <div className="max-w-xs mx-auto h-32 flex items-center">
                            <Select value={selectedLevel} onValueChange={setSelectedLevel}>
                                <SelectTrigger>
                                    <SelectValue placeholder={selectedSyllabus === "KTU" ? "Select Semester" : "Select Grade"} />
                                </SelectTrigger>
                                <SelectContent>
                                    {getLevelOptions().map((option) => (
                                        <SelectItem key={option.value} value={option.value}>
                                            {option.label}
                                        </SelectItem>
                                    ))}
                                </SelectContent>
                            </Select>
                        </div>
                    )}

                    {currentStep === 4 && (
                        <div className="text-center space-y-4 h-32 flex flex-col items-center justify-center">
                            <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
                            <p className="font-semibold">
                                You're all set with <Badge>{selectedSyllabus}</Badge> - <Badge>{selectedLevel}</Badge>
                            </p>
                        </div>
                    )}

                    <div className="flex justify-between pt-6">
                        <Button variant="outline" onClick={handleBack} disabled={currentStep === 1} className="bg-transparent">
                            <ChevronLeft className="h-4 w-4 mr-2" />Back
                        </Button>

                        {currentStep < 4 ? (
                            <Button onClick={handleNext} disabled={!canProceed()}>
                                Next <ChevronRight className="h-4 w-4 ml-2" />
                            </Button>
                        ) : (
                            <Button onClick={handleComplete} className="bg-green-600 hover:bg-green-700">
                                Start Learning
                            </Button>
                        )}
                    </div>
                </div>
            </DialogContent>
        </Dialog>
    )
}