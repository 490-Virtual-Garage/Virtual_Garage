import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";

function Login() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background login">
        <div className="flex flex-col"> 
            <h1>Login</h1>
            
        </div>
      </main>

      <Footer />
    </div>
  )
}

export default Login