import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'

function Header() {
    const { currentUser, loading } = useAuth()

    const homePath = currentUser ? '/dashboard' : '/'

    return (
        <header className="header">
          <h1>
            <Link to={homePath} className="text-white">
                Virtual Garage
            </Link>
          </h1>
        </header>
    )
}

export default Header