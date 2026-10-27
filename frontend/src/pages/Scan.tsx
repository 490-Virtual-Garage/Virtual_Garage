import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";

function Scan() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background landing">
        <h1 className="text-white">Scan</h1>
      </main>

      <Footer />
    </div>
  )
}

export default Scan