import React, { useEffect, useContext, useState } from 'react'
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    onAuthStateChanged,
    setPersistence,
    browserSessionPersistence,
    getIdToken,
    type User,
    type UserCredential
} from 'firebase/auth'
import { auth } from '../firebase'

type AuthContextType = {
  currentUser: User | null //currentUser is either authenticated or not
  loading: boolean
  register: (email: string, password: string) => Promise<UserCredential>
  login: (email: string, password: string) => Promise<UserCredential>
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
    const context = useContext(AuthContext)

    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }

    return context
}

async function syncUser(user: User) {
    const token = await getIdToken(user)
    const res = await fetch(`http://localhost:8001/users`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error(`User sync failed: ${res.status}`)
}

type AuthProviderProps = {
    children: React.ReactNode
}

export function AuthProvider({ children }: AuthProviderProps) {
    const [currentUser, setCurrentUser] = useState<User | null>(null)
    const [loading, setLoading] = useState(true)

    //Session persist on signup
    async function register(
        email: string,
        password: string
    ): Promise<UserCredential> {
        await setPersistence(auth, browserSessionPersistence)
        const cred = await createUserWithEmailAndPassword(auth, email, password)
        await syncUser(cred.user)
        return cred
    }

    //Session persist on login
    async function login(
        email: string,
        password: string
    ): Promise<UserCredential> {
        await setPersistence(auth, browserSessionPersistence)
        return signInWithEmailAndPassword(auth, email, password)
    }

    //Checks current user status
    useEffect(() => {
        const unsubscribe = onAuthStateChanged(auth, user => {
        setCurrentUser(user)
        setLoading(false)
        })

        return unsubscribe
    }, [])

    const value: AuthContextType = {
        currentUser,
        loading,
        register,
        login
    }

    return (
    <AuthContext.Provider value={value}>
        {children}
    </AuthContext.Provider>
    )
}
