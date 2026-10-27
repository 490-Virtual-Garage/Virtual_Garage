import { Link } from 'react-router-dom'
import Footer from "../components/Footer";
import Header from "../components/Header";

function History() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="background landing">
        <h1 className="text-white">History</h1>
      </main>

      <Footer />
    </div>
  )
}

export default History