import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";

function Landing() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background landing">
        <h2 className="landing-title">Welcome to your garage</h2>
        <p className="landing-tagline">Keep your cars, parts, and projects in one place.</p>

        <nav className="landing-nav">
          <Link to="/scan" className="landing-btn landing-btn-primary">Scan Your Car</Link>
          <Link to="/history" className="landing-btn">Garage History</Link>
        </nav>
      </main>

      <Footer />
    </div>
  )
}

export default Landing