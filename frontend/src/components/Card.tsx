import type { ReactNode } from "react";

type CardProps = {
  children?: ReactNode;
  className?: string;
};

export default function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`w-full max-w-sm p-8 bg-black/80 border border-slate-700 rounded-xl shadow-lg text-white ${className}`}>
      {children}
    </div>
  );
}