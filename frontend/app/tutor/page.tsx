"use client"

import React, { useState, useRef, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Badge } from "@/components/ui/badge"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Send, Bot, User, Loader2, BookOpen, ChevronDown, FileText } from "lucide-react"
import { cn } from "@/lib/utils"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

// --- 1. IMPORT THE NEW MARKDOWN RENDERER ---
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface Message {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: Date
  sources?: any[]
}

export default function TutorPage() {
  const { currentSubject } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [availableSources, setAvailableSources] = useState<string[]>([])
  const [selectedSources, setSelectedSources] = useState<string[]>([])
  const scrollAreaRef = useRef<HTMLDivElement>(null)

    // Fetch documents when the selected subject changes.
    useEffect(() => {
        if (currentSubject) {
            setMessages([
                {
                    id: "1",
                    content: `Hello! I'm your AI tutor for **${currentSubject.name}**. Ask me anything about your course materials.`,
                    role: "assistant",
                    timestamp: new Date(),
                },
            ]);

            const fetchDocuments = async () => {
                try {
                    const response = await fetch(
                        `${process.env.NEXT_PUBLIC_API_URL}/documents?subject_code=${currentSubject.code}`,
                        {
                            headers: {
                                'Authorization': `Bearer ${token}`
                            }
                        }
                    )
                    const data = await response.json()
                    if (data.documents) {
                        setAvailableSources(data.documents)
                        setSelectedSources(data.documents)
                    }
                } catch (error) {
                    console.error("Failed to fetch documents:", error)
                }
            }
            fetchDocuments()
        }
    }, [currentSubject, token])

  // Effect to scroll to bottom when new messages are added
  useEffect(() => {
    const scrollViewport = scrollAreaRef.current?.querySelector('[data-radix-scroll-area-viewport]');
    if (scrollViewport) {
      scrollViewport.scrollTop = scrollViewport.scrollHeight;
    }
  }, [messages])

  const handleSourceToggle = (sourceName: string) => {
    setSelectedSources((prev) =>
        prev.includes(sourceName) ? prev.filter((s) => s !== sourceName) : [...prev, sourceName]
    )
  }

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading || !currentSubject) return

    const userMessage: Message = { id: Date.now().toString(), content: inputValue.trim(), role: "user", timestamp: new Date() }
    setMessages((prev) => [...prev, userMessage])
    const currentInput = inputValue.trim();
    setInputValue("")
    setIsLoading(true)

    // Add empty assistant message initially
    const assistantMessageId = (Date.now() + 1).toString()
    setMessages((prev) => [...prev, {
      id: assistantMessageId, content: "",
      role: "assistant", timestamp: new Date(), sources: []
    }])

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/ask`, {
        method: "POST", headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ query: currentInput, subject_code: currentSubject.code, sources: selectedSources }),
      });
      if (!response.ok) throw new Error("The request to the AI tutor failed.");
      
      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      if (!reader) throw new Error("Stream not readable");

      let streamedText = "";
      
      while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          const chunk = decoder.decode(value, { stream: true });
          const lines = chunk.split('\\n');
          
          for (const line of lines) {
              if (line.trim() === '') continue;
              try {
                  const data = JSON.parse(line);
                  setMessages((prev) => 
                    prev.map(msg => {
                      if (msg.id === assistantMessageId) {
                        if (data.type === "sources") {
                           return { ...msg, sources: data.data };
                        } else if (data.type === "token") {
                           streamedText += data.content;
                           return { ...msg, content: streamedText };
                        }
                      }
                      return msg;
                    })
                  );
              } catch (e) {
                 console.error("Failed to parse stream JSON chunk", e, line);
              }
          }
      }
    } catch (error) {
      console.error("Error asking AI tutor:", error)
      setMessages((prev) => 
        prev.map(msg => msg.id === assistantMessageId ? { ...msg, content: "Sorry, I encountered an error. Please try again." } : msg)
      )
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const formatTime = (date: Date) => date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })

  if (!currentSubject) {
    return <div className="text-center text-muted-foreground">Please select a subject to chat with the AI Tutor.</div>
  }

  return (
      <div className="flex flex-col h-full max-h-[calc(100vh-8rem)]">
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-foreground">{currentSubject.name} AI Tutor</h1>
          <p className="text-muted-foreground">Ask questions about your {currentSubject.code} course materials.</p>
        </div>
        <Card className="flex-1 flex flex-col min-h-0">
          <CardHeader className="flex-shrink-0">
            <CardTitle className="flex items-center gap-2"><Bot className="w-5 h-5 text-primary"/>Chat with {currentSubject.name} AI</CardTitle>
            <Collapsible className="mt-2">
              <CollapsibleTrigger asChild>
                <Button variant="outline" size="sm" className="w-full justify-between bg-transparent">
                  <span>Sources ({selectedSources.length}/{availableSources.length} selected)</span><ChevronDown className="h-4 w-4"/>
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent className="p-4 border rounded-md mt-2 space-y-2">
                <Label>Select documents for the AI to reference:</Label>
                {availableSources.map((source) => (
                    <div key={source} className="flex items-center space-x-2">
                      <Checkbox id={source} checked={selectedSources.includes(source)} onCheckedChange={() => handleSourceToggle(source)}/>
                      <Label htmlFor={source} className="text-xs font-normal cursor-pointer">{source}</Label>
                    </div>
                ))}
              </CollapsibleContent>
            </Collapsible>
          </CardHeader>
          <CardContent className="flex-1 flex flex-col min-h-0 p-0">
            <ScrollArea ref={scrollAreaRef} className="flex-1 px-6">
              <div className="space-y-4 pb-4">
                {messages.map((message) => (
                    <div key={message.id} className={cn("flex items-start gap-3 text-sm", message.role === "user" ? "justify-end" : "justify-start")}>
                      {message.role === "assistant" && <Avatar className="w-8 h-8 shrink-0"><AvatarFallback className="bg-primary text-primary-foreground"><Bot className="w-4 h-4"/></AvatarFallback></Avatar>}
                      <div className={cn("max-w-[80%] rounded-lg px-4 py-3", message.role === "user" ? "bg-primary text-primary-foreground" : "bg-muted")}>

                        {/* --- 2. REPLACE <p> WITH <ReactMarkdown> --- */}
                        {/* We use the `prose` class from the typography plugin for styling */}
                        <div className="prose prose-sm dark:prose-invert max-w-none">
                          <ReactMarkdown remarkPlugins={[remarkGfm]}>
                            {message.content}
                          </ReactMarkdown>
                        </div>

                        {message.sources && message.sources.length > 0 && (
                            <div className="mt-3 pt-2 border-t border-muted-foreground/20">
                              <h4 className="text-xs font-semibold mb-1">Sources:</h4>
                              <div className="flex flex-wrap gap-2">
                                {message.sources.map((source, index) => (
                                    <Badge key={index} variant="secondary" className="text-xs">
                                      <FileText className="w-3 h-3 mr-1"/>{source.source.split('/').pop()} (p. {source.page})
                                    </Badge>
                                ))}
                              </div>
                            </div>
                        )}
                        <p className={cn("text-xs mt-2 opacity-70 text-right", message.role === "user" ? "text-primary-foreground/70" : "text-muted-foreground/70")}>{formatTime(message.timestamp)}</p>
                      </div>
                      {message.role === "user" && <Avatar className="w-8 h-8 shrink-0"><AvatarFallback><User className="w-4 h-4"/></AvatarFallback></Avatar>}
                    </div>
                ))}
                {isLoading && (
                    <div className="flex gap-3 justify-start"><Avatar className="w-8 h-8 mt-1"><AvatarFallback className="bg-primary text-primary-foreground"><Bot className="w-4 h-4"/></AvatarFallback></Avatar><div className="bg-muted text-muted-foreground rounded-lg px-4 py-3 text-sm"><LoadingSpinner size="sm"/></div></div>
                )}
              </div>
            </ScrollArea>
            <div className="flex-shrink-0 border-t p-4">
              <div className="flex gap-2">
                <Input placeholder={`Ask a question about ${currentSubject.name}...`} value={inputValue} onChange={(e) => setInputValue(e.target.value)} onKeyPress={handleKeyPress} disabled={isLoading}/>
                <Button onClick={handleSendMessage} disabled={!inputValue.trim() || isLoading} size="icon" className="shrink-0"><Send className="w-4 h-4"/></Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
  )
}