import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";

function Landing() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background mainContent flex-1 px-4">
        <nav className="flex items-center flex-col justify-center border border-gray-500 bg-black text-white gap-6 min-h-screen w-3/4 opacity-90">
          <h2 className="text-5xl opacity-100">Menu</h2>
          <Link to="/signup" className="text-3xl opacity-100">Sign Up</Link>
          <Link to="/login" className="text-3xl opacity-100">Log in</Link>
          <Link to="/" className="text-3xl opacity-100">Option 3</Link>
        </nav>
      </main>

      <Footer />
    </div>
  )
}

export default Landing