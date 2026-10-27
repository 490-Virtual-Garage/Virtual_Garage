import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getAuth, signOut } from "firebase/auth";
import '../firebase';
import Footer from "../components/Footer";
import Header from "../components/Header";

function Dashboard() {
  //Initialize nav and useStates
  const navigate = useNavigate()
  const [error, setError] = useState('')

  function handleSignOut() {
    setError('')
    
    //Assign Auth object
    const auth = getAuth();

    // Sign out the user
    signOut(auth)
      .then(() => {
        console.log('User signed out successfully!');
        //Move to landing after proper signout
        navigate('/')
    })

    //Errors
    .catch((error) => {
      const errorCode = error.code;
      const errorMessage = error.message;
      console.error(errorCode, errorMessage)
      setError(errorMessage)
    });
  }

  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background landing">
        <h2 className="landing-title">Welcome to your garage</h2>
        <p className="landing-tagline">Keep your cars, parts, and projects in one place.</p>

        <nav className="landing-nav">
          <Link to="/scan" className="landing-btn landing-btn-primary">Scan Your Car</Link>
          <Link to="/history" className="landing-btn">Garage History</Link>
          <button onClick={handleSignOut} className="landing-btn cursor-pointer">Logout</button>
          {error && <p className="text-red-500">{error}</p>}
        </nav>
      </main>

      <Footer />
    </div>
  )
}

export default Dashboard