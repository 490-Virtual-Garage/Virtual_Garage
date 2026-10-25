import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";

function Login() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background register">
        <div className="flex flex-col"> 
            <h1>Register</h1>
            
        </div>
      </main>

      <Footer />
    </div>
  )
}

export default Login