"use client"

import { Button } from "@/components/ui/button"
import { ArrowRight, Menu, BookOpen, Brain, Target, Users } from "lucide-react"
import { LineShadowText } from "@/components/line-shadow-text"
import { ShimmerButton } from "@/components/shimmer-button"
import { useState } from "react"
import Link from "next/link"

export default function HomePage() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <div className="min-h-screen bg-background">
      {/* Header Navigation */}
      <header className="relative z-10 flex items-center justify-between px-4 sm:px-6 py-4 lg:px-12 border-b border-border">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 sm:w-10 sm:h-10 lg:w-12 lg:h-12 bg-primary rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 sm:w-6 sm:h-6 lg:w-7 lg:h-7 text-primary-foreground" />
            </div>
            <span className="text-xl sm:text-2xl lg:text-3xl font-bold text-foreground">Learnix</span>
          </div>
        </div>

        <nav className="hidden md:flex items-center space-x-6 lg:space-x-8">
          <a
            href="#features"
            className="text-muted-foreground hover:text-foreground transition-colors text-sm lg:text-base"
          >
            Features
          </a>
          <a
            href="#pricing"
            className="text-muted-foreground hover:text-foreground transition-colors text-sm lg:text-base"
          >
            Pricing
          </a>
          <a
            href="#about"
            className="text-muted-foreground hover:text-foreground transition-colors text-sm lg:text-base"
          >
            About
          </a>
          <a
            href="#contact"
            className="text-muted-foreground hover:text-foreground transition-colors text-sm lg:text-base"
          >
            Contact
          </a>
        </nav>

        {/* Mobile menu button */}
        <button className="md:hidden text-foreground p-2" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
          <Menu className="w-6 h-6" />
        </button>

        <ShimmerButton className="hidden md:flex bg-primary hover:bg-primary/90 text-primary-foreground px-4 lg:px-6 py-2 rounded-lg text-sm lg:text-base font-medium shadow-lg">
          Get Started
        </ShimmerButton>
      </header>

      {mobileMenuOpen && (
        <div className="md:hidden absolute top-16 left-0 right-0 bg-card backdrop-blur-sm border-b border-border z-20">
          <nav className="flex flex-col space-y-4 px-6 py-6">
            <a href="#features" className="text-muted-foreground hover:text-foreground transition-colors">
              Features
            </a>
            <a href="#pricing" className="text-muted-foreground hover:text-foreground transition-colors">
              Pricing
            </a>
            <a href="#about" className="text-muted-foreground hover:text-foreground transition-colors">
              About
            </a>
            <a href="#contact" className="text-muted-foreground hover:text-foreground transition-colors">
              Contact
            </a>
            <ShimmerButton className="bg-primary hover:bg-primary/90 text-primary-foreground px-6 py-2.5 rounded-lg text-sm font-medium shadow-lg w-fit">
              Get Started
            </ShimmerButton>
          </nav>
        </div>
      )}

      {/* Hero Section */}
      <main className="relative flex flex-col items-center justify-center min-h-[calc(100vh-80px)] px-4 sm:px-6 lg:px-12 text-center">
        <div className="mb-6 sm:mb-8">
          <div className="inline-flex items-center bg-primary/10 border border-primary/20 rounded-full px-4 py-2">
            <span className="text-foreground text-sm font-medium">AI-Powered Exam Preparation</span>
          </div>
        </div>

        <h1 className="text-foreground text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold leading-tight mb-6 text-balance max-w-4xl">
          Master Your Exams with{" "}
          <LineShadowText className="italic font-light text-primary" shadowColor="rgba(21, 128, 61, 0.3)">
            AI Intelligence
          </LineShadowText>
        </h1>

        <p className="text-muted-foreground text-lg sm:text-xl md:text-2xl mb-8 max-w-3xl text-pretty">
          Transform your study experience with personalized AI tutoring, smart question generation, and adaptive
          learning paths designed for exam success.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 mb-12">
          <Link href="/dashboard">
            <Button className="group relative bg-primary hover:bg-primary/90 text-primary-foreground px-8 py-3 rounded-lg text-lg font-semibold flex items-center gap-2 shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-105">
              Launch App
              <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform duration-300" />
            </Button>
          </Link>
          <Button
            variant="outline"
            className="px-8 py-3 rounded-lg text-lg font-semibold border-border hover:bg-muted bg-transparent"
          >
            Watch Demo
          </Button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl w-full">
          <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
              <BookOpen className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-card-foreground mb-2">Smart Study Plans</h3>
            <p className="text-muted-foreground text-sm">
              Personalized learning paths adapted to your pace and exam requirements.
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Target className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-card-foreground mb-2">Question Explorer</h3>
            <p className="text-muted-foreground text-sm">
              AI-generated practice questions with detailed explanations and analytics.
            </p>
          </div>

          <div className="bg-card border border-border rounded-lg p-6 text-center hover:shadow-lg transition-shadow">
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center mx-auto mb-4">
              <Users className="w-6 h-6 text-primary" />
            </div>
            <h3 className="text-lg font-semibold text-card-foreground mb-2">AI Tutor</h3>
            <p className="text-muted-foreground text-sm">
              24/7 intelligent tutoring with instant answers to your study questions.
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
