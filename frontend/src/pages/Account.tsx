import { Link, useNavigate } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";
import { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';

function Account() {
    const navigate = useNavigate()
    const { deleteAccount } = useAuth()

    const [error, setError] = useState('')

    //Delete account when user clicks delete account button
    async function handleDeleteAccount() {
        setError('')

        try {
            await deleteAccount()

            console.log("Account deleted")

            navigate('/')
        } catch (error: unknown) {
        if (error instanceof Error) {
            console.error(error.message)
            setError(error.message)
        } else {
            setError('An unexpected error occurred.')
        }
        }
    }

    return (
        <div className="flex flex-col min-h-screen">
        <Header />

        <main className="background landing">
            <h1 className="text-white">Account</h1>
            <button className="cursor-pointer border border-black bg-red-600 hover:bg-red-800" onClick={handleDeleteAccount}>
                Delete Account
            </button>
            <button className="cursor-pointer">Update Account</button>
        </main>

        <Footer />
        </div>
    )
}

export default Account