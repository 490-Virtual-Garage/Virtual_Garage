import { Link } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import NavMenu from '../components/NavMenu'

function Header() {
    const { currentUser } = useAuth()

    const homePath = currentUser ? '/dashboard' : '/'

    return (
        <header className="header">
          <h1>
            <Link to={homePath} className="text-white">
                Virtual Garage
            </Link>
          </h1>
          {currentUser && (
            <div className="nav-menu-wrapper">
              <NavMenu />
            </div>
          )}
        </header>
    )
}

export default Header