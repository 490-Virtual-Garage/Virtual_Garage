import React, { useEffect, useContext, useState } from 'react'
import {
    createUserWithEmailAndPassword,
    signInWithEmailAndPassword,
    onAuthStateChanged,
    setPersistence,
    browserSessionPersistence,
    getIdToken,
    deleteUser,
    type User,
    type UserCredential
} from 'firebase/auth'
import { auth } from '../firebase'

type AuthContextType = {
  currentUser: User | null //currentUser is either authenticated or not
  loading: boolean
  register: (email: string, password: string) => Promise<UserCredential>
  login: (email: string, password: string) => Promise<UserCredential>
  deleteAccount: () => Promise<void>
}

const AuthContext = React.createContext<AuthContextType | undefined>(undefined)

export function useAuth() {
    const context = useContext(AuthContext)

    if (!context) {
        throw new Error('useAuth must be used within an AuthProvider')
    }

    return context
}

//Add user to backend database after registration
async function syncUser(user: User) {
    const token = await getIdToken(user)
    const res = await fetch(`http://localhost:8001/users`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error(`User sync failed: ${res.status}`)
}

//Delete user from backend database when account is deleted
async function requestDeleteUser(user: User) {
    const token = await getIdToken(user)
    const res = await fetch(`http://localhost:8001/users`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
    })
    if (!res.ok) throw new Error(`User delete failed: ${res.status}`)
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

    //Delete firebase and db user
    async function deleteAccount() {
        if (!currentUser) {
            throw new Error('No user is currently logged in.')
        }

        await requestDeleteUser(currentUser)
        await deleteUser(currentUser)
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
        login,
        deleteAccount
    }

    return (
    <AuthContext.Provider value={value}>
        {children}
    </AuthContext.Provider>
    )
}
