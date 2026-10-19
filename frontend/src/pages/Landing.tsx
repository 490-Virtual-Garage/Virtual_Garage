import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";

function Landing() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background landing">
        <h2 className="landing-title">Your garage, always open</h2>
        <p className="landing-tagline">Keep your cars, parts, and projects in one place.</p>

        <nav className="landing-nav">
          <Link to="/signup" className="landing-btn landing-btn-primary">Sign up</Link>
          <Link to="/login" className="landing-btn">Log in</Link>
          <Link to="/garage" className="landing-btn">Browse garage</Link>
        </nav>
      </main>

      <Footer />
    </div>
  )
}

export default Landing