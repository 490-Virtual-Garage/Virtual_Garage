import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getAuth, createUserWithEmailAndPassword } from "firebase/auth";
import '../firebase';
import Footer from "../components/Footer";
import Header from "../components/Header";
import Card from '../components/Card';

function Register() {
  //Initialize nav and useStates
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  function handleRegister() {
    setError('')
    
    //Assign Auth object
    const auth = getAuth();

    //Create user function
    createUserWithEmailAndPassword(auth, email, password)
      .then((userCredential) => {
        //Signed up
        const user = userCredential.user;
        console.log('created:', user.uid)

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

      <main className="background register">
        <Card className="flex flex-col gap-4">
          <div>
            <h1>Sign Up</h1>
            <h2>Create your account</h2>
          </div>
          <form
            onSubmit={(e) => {
              e.preventDefault()
              handleRegister()
            }}
            className="flex flex-col gap-4"
          >
            <input
              className="bg-gray-900 px-2"
              type="email"
              name="email"
              placeholder="Enter Email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              autoComplete="email"
              required
            />

            <input
              className="bg-gray-900 px-2"
              type="password"
              name="password"
              placeholder="Enter Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />

            {error && <p className="text-red-500">{error}</p>}
            
            <button className="flex justify-center self-center w-fit bg-gray-900 px-6 py-2 hover:bg-gray-600 cursor-pointer" type="submit">Create Account</button>
          </form>
          <p>Already have an account? <Link to="/login" className="text-blue-500 hover:underline cursor-pointer">Login</Link></p>
        </Card>
      </main>

      <Footer />
    </div>
  )
}

export default Register