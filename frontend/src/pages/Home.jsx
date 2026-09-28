import '../App.css'
import Footer from "../components/Footer.jsx";
import Header from "../components/Header.jsx";

function Home() {
  return (
    <>
        <Header />

        <main className="flex items-center justify-center flex-col">
            <p>Menu</p>
            <p>Option 1</p>
            <p>Option 2</p>
            <p>Option 3</p>

        </main>

        <Footer />
    </>
  )
}

export default Home
