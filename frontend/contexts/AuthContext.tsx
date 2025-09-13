"use client"

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';

interface User {
    name: string;
    email: string;
    syllabus?: string;
    level?: string;
}

interface Subject {
    code: string;
    name: string;
}

interface AuthContextType {
    user: User | null;
    token: string | null;
    isFirstLogin: boolean;
    currentSubject: Subject | null;
    isAuthenticated: boolean;
    login: (userData: User, token: string, isFirst: boolean) => void;
    logout: () => void;
    updateUserPreferences: (data: { syllabus: string; level: string }) => void;
    setCurrentSubject: (subject: Subject) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: ReactNode }) => {
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isFirstLogin, setIsFirstLogin] = useState(false);
    const [currentSubject, setCurrentSubjectState] = useState<Subject | null>(null);
    const router = useRouter();

    useEffect(() => {
        // On initial load, try to rehydrate auth state from localStorage
        const storedToken = localStorage.getItem('token');
        const storedUser = localStorage.getItem('user');
        const storedIsFirstLogin = localStorage.getItem('is_first_login') === 'true';

        if (storedToken && storedUser) {
            setUser(JSON.parse(storedUser));
            setToken(storedToken);
            setIsFirstLogin(storedIsFirstLogin);
        }
    }, []);

    const login = (userData: User, token: string, isFirst: boolean) => {
        localStorage.setItem('user', JSON.stringify(userData));
        localStorage.setItem('token', token);
        localStorage.setItem('is_first_login', String(isFirst));

        setUser(userData);
        setToken(token);
        setIsFirstLogin(isFirst);
    };

    const logout = () => {
        localStorage.clear();
        setUser(null);
        setToken(null);
        setIsFirstLogin(false);
        setCurrentSubjectState(null);
        router.push('/login');
    };

    const updateUserPreferences = (data: { syllabus: string; level: string }) => {
        if (user) {
            const updatedUser = { ...user, ...data };
            setUser(updatedUser);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            // No longer first login after this completes
            setIsFirstLogin(false);
            localStorage.removeItem('is_first_login');
        }
    };

    const setCurrentSubject = (subject: Subject) => {
        setCurrentSubjectState(subject);
        // You could also save this to localStorage to remember the user's last subject
    };

    return (
        <AuthContext.Provider value={{
            user,
            token,
            isFirstLogin,
            currentSubject,
            isAuthenticated: !!token,
            login,
            logout,
            updateUserPreferences,
            setCurrentSubject,
        }}>
            {children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
};