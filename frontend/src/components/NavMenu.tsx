import { useState } from "react";
import { Link } from "react-router";

export default function NavMenu() {
  const [open, setOpen] = useState(false);

  return (
    <div className="relative">
      <button onClick={() => setOpen(!open)} className="text-white text-xl cursor-pointer">
        Menu
      </button>

      {open && (
        <div className="absolute w-30 top-full mt-2 border border-white bg-neutral-900 flex flex-col text-white pl-1">
          <Link to="/account" onClick={() => setOpen(false)}>Account</Link>
          <Link to="/scan" onClick={() => setOpen(false)}>Scan Your Car</Link>
          <Link to="/history" onClick={() => setOpen(false)}>Garage History</Link>
          <Link to="/vehicles" onClick={() => setOpen(false)}>Vehicles</Link>
        </div>
      )}
    </div>
  );
}