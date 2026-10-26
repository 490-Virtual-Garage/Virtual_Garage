import { Link } from "react-router-dom";

function Header() {
  return (
    <header className="header">
      <h1 className="text-white">
        <Link to="/">Virtual Garage</Link>
      </h1>
    </header>
  )
}

export default Header