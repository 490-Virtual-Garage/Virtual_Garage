import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

//Authenticated routes component
export default function PrivateRoute() {
    const { currentUser, loading } = useAuth()

    if (loading) {
        return <p>Checking authentication...</p>
    }

    if (!currentUser) {
        return <Navigate to="/login" replace />
    }

    return <Outlet />
}