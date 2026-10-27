import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getAuth, signInWithEmailAndPassword } from "firebase/auth";
import '../firebase';
import Footer from "../components/Footer";
import Header from "../components/Header";
import Card from '../components/Card';

function Login() {
  //Initialize nav and useStates
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  function handleLogin() {
    setError('')
    
    //Assign Auth object
    const auth = getAuth();

    //Create user function
    signInWithEmailAndPassword(auth, email, password)
      .then((userCredential) => {
        //Logged in
        const user = userCredential.user;
        console.log('User signed in:', user.email)

        //Move to dashboard after proper signup
        navigate('/dashboard')
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

      <main className="background login">
        <Card className="flex flex-col gap-4">
          <div>
            <h1>Login</h1>
            <h2>Welcome Back</h2>
          </div>
          
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleLogin()
            }}
            className="flex flex-col gap-4"
          >
            <input
              type="email"
              name="email"
              placeholder="Enter Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />

            <input
              type="password"
              name="password"
              placeholder="Enter Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />

            <button type="submit">Log In</button>
          </form>
          <p>Don't have an account? <Link to="/signup" className="text-blue-500 hover:underline">Sign up</Link></p>
        </Card>  
      </main>

      <Footer />
    </div>
  )
}

export default Login