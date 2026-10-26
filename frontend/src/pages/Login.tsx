import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";
import Card from '../components/Card';

function Login() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background login">
        <Card className="flex flex-col gap-4">
          <div>
            <h1>Sign Up</h1>
            <h2>Create your account</h2>
          </div>
          <input type="text" id="myTextbox1" name="myTextbox1" placeholder="Enter Email/Username"/>
          <input type="text" id="myTextbox2" name="myTextbox2" placeholder="Enter Password"/>

          {/* Work on button later when doing auth */}
          <button>Login</button>
          <p>Don't have an account? <Link to="/signup" className="text-blue-500 hover:underline">Sign up</Link></p>
        </Card>  
      </main>

      <Footer />
    </div>
  )
}

export default Login