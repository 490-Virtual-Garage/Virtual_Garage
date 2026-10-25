import type { ReactNode } from "react";

type CardProps = {
  children?: ReactNode;
  className?: string;
};

export default function Card({ children, className = "" }: CardProps) {
  return (
    <div className={`w-full max-w-sm p-8 bg-slate-900 border border-slate-700 rounded-xl shadow-lg ${className}`}>
      {children}
    </div>
  );
}