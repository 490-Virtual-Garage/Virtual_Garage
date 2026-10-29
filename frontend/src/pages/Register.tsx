import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/AuthContext'
import Footer from '../components/Footer'
import Header from '../components/Header'
import Card from '../components/Card'

function Register() {
  const navigate = useNavigate()
  const { register } = useAuth()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function handleRegister() {
    setError('')

    try {
      const { user } = await register(email, password)

      console.log('created:', user.uid)

      navigate('/dashboard')
    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error(error.message)
        setError(error.message)
      } else {
        setError('An unexpected error occurred.')
      }
    }
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
            onSubmit={e => {
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
              onChange={e => setEmail(e.target.value)}
              autoComplete="email"
              required
            />

            <input
              className="bg-gray-900 px-2"
              type="password"
              name="password"
              placeholder="Enter Password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="new-password"
              required
            />

            {error && <p className="text-red-500">{error}</p>}

            <button
              className="flex justify-center self-center w-fit bg-gray-900 px-6 py-2 hover:bg-gray-600 cursor-pointer"
              type="submit"
            >
              Create Account
            </button>
          </form>

          <p>
            Already have an account?{' '}
            <Link
              to="/login"
              className="text-blue-500 hover:underline cursor-pointer"
            >
              Login
            </Link>
          </p>
        </Card>
      </main>

      <Footer />
    </div>
  )
}

export default Register
