import { useEffect } from "react";
import { Anchor, ArrowLeft, Home } from "lucide-react";
import "./NotFound.css";

function NotFound() {
  useEffect(() => {
    const savedTheme = localStorage.getItem("freight-theme") || "dark";
    document.documentElement.dataset.theme = savedTheme;
  }, []);

  return (
    <div className="not-found-page">
      <div className="not-found-card">
        <div className="not-found-icon">
          <Anchor size={34} />
        </div>

        <span className="not-found-code">404</span>

        <h1>This port doesn't exist.</h1>

        <p>
          The route you're trying to reach couldn't be found in Freight
          Predictor.
        </p>

        <div className="not-found-actions">
          <a href="/" className="primary-btn">
            <Home size={16} />
            Back to Dashboard
          </a>

          <button
            className="secondary-btn"
            onClick={() => window.history.back()}
          >
            <ArrowLeft size={16} />
            Go Back
          </button>
        </div>
      </div>
    </div>
  );
}

export default NotFound;