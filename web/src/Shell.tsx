import { useState, type ReactNode } from "react";

const root = document.documentElement;

// Two looks: "dark" is the coffee house of the Streamlit app, "light" is VerifAI's cream. Shared with the offline report.
function ThemeToggle() {
  const [theme, setTheme] = useState(root.dataset.theme);
  const next = theme === "light" ? "dark" : "light";
  const flip = () => {
    root.dataset.theme = next;
    try {
      localStorage.setItem("dejavu:theme", next);
    } catch {
      /* storage blocked: the choice lasts this visit only */
    }
    setTheme(next);
  };
  return (
    <button className="icon" onClick={flip} aria-label={next === "light" ? "Switch to the cream theme" : "Switch to the coffee theme"}
      title={next === "light" ? "Cream theme" : "Coffee theme"}>
      {next === "light" ? (
        <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round">
          <circle cx="10" cy="10" r="3.6" />
          <path d="M10 1.8v2M10 16.2v2M1.8 10h2M16.2 10h2M4.2 4.2l1.4 1.4M14.4 14.4l1.4 1.4M4.2 15.8l1.4-1.4M14.4 5.6l1.4-1.4" />
        </svg>
      ) : (
        <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round">
          <path d="M16.5 12.6A7 7 0 0 1 7.4 3.5a7 7 0 1 0 9.1 9.1z" />
        </svg>
      )}
    </button>
  );
}

// The bar every screen shares: name on the left, actions and the theme toggle on the right.
export function Shell({ tag, actions, children }: { tag?: ReactNode; actions?: ReactNode; children: ReactNode }) {
  return (
    <div className="app">
      <header className="bar">
        <a className="brand" href="#">Dejavu</a>
        <span className="tagline">code similarity review</span>
        {tag && <span className="tag">{tag}</span>}
        <span className="grow" />
        {actions}
        <ThemeToggle />
      </header>
      {children}
    </div>
  );
}
