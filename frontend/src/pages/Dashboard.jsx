import '../App.css'
import Footer from "../components/Footer.jsx";
import Header from "../components/Header.jsx";

function Dashboard() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background mainContent flex-1 px-4">
        <nav className="flex items-center flex-col border border-gray-500 bg-black text-white gap-6 px-[5%] py-[2%]">
          <h2 className="text-5xl">Menu</h2>
          <p className="text-3xl">Sign Up</p>
          <p className="text-3xl">Log in</p>
          <p className="text-3xl">Option 3</p>
        </nav>
      </main>

      <Footer />
    </div>
  )
}

export default Dashboard
