import { Routes, Route } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import Landing from './pages/Landing'
import Register from './pages/Register'
import Login from './pages/Login'
import History from './pages/History'
import Scan from './pages/Scan'
import PrivateRoute from './components/PrivateRoute'

function App() {
    return (
        <Routes>
            {/* Public routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/signup" element={<Register />} />
            <Route path="/login" element={<Login />} />

            {/* Protected routes when authenticated */}
            <Route element={<PrivateRoute />}>
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/history" element={<History />} />
                <Route path="/scan" element={<Scan />} />
            </Route>
        </Routes>
    )
}

export default App