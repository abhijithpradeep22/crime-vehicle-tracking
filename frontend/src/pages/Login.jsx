import { useState } from "react";
import { apiRequest } from "../api/client";
import { useNavigate } from "react-router-dom";
import "./Login.css";

export default function Login() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const res = await apiRequest("/auth/login", "POST", { username, password });
      localStorage.setItem("user_id", res.user_id);
      localStorage.setItem("username", res.username);
      navigate("/dashboard");
    } catch (err) {
      setError("ACCESS DENIED — Invalid credentials");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-page">
      {/* Animated background grid */}
      <div className="bg-grid" />
      <div className="scan-line" />

      <div className="login-wrapper">
        {/* Corner brackets */}
        <span className="bracket tl" />
        <span className="bracket tr" />
        <span className="bracket bl" />
        <span className="bracket br" />

        <div className="login-card">
          {/* Header */}
          <div className="card-header">
            <div className="status-bar">
              <span className="status-dot" />
              <span className="status-text">LAW ENFORCEMENT ACCESS ONLY</span>
            </div>
            <div className="logo-area">
              <div className="shield-icon">
                <svg viewBox="0 0 40 46" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 2L3 9V22C3 31.9 10.5 41.2 20 44C29.5 41.2 37 31.9 37 22V9L20 2Z"
                    stroke="#00e5ff" strokeWidth="1.5" fill="rgba(0,229,255,0.05)" />
                  <path d="M13 22L18 27L28 17" stroke="#00e5ff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </div>
              <div className="title-block">
                <h1 className="login-title">Multi-Camera Crime Vehicle Detection System</h1>
              </div>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleLogin} className="login-form">
            <div className="field-group">
              <label className="field-label">USERNAME</label>
              <div className="input-wrap">
                <svg className="field-icon" viewBox="0 0 24 24" fill="none">
                  <circle cx="12" cy="8" r="4" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                <input
                  type="text"
                  placeholder="Enter username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  autoComplete="username"
                  required
                />
              </div>
            </div>

            <div className="field-group">
              <label className="field-label">PASSWORD</label>
              <div className="input-wrap">
                <svg className="field-icon" viewBox="0 0 24 24" fill="none">
                  <rect x="5" y="11" width="14" height="10" rx="2" stroke="currentColor" strokeWidth="1.5"/>
                  <path d="M8 11V7a4 4 0 0 1 8 0v4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
                  <circle cx="12" cy="16" r="1.5" fill="currentColor"/>
                </svg>
                <input
                  type="password"
                  placeholder="Enter password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                  required
                />
              </div>
            </div>

            {error && (
              <div className="error-msg">
                <svg viewBox="0 0 24 24" fill="none" width="14" height="14">
                  <circle cx="12" cy="12" r="9" stroke="#ff4d4d" strokeWidth="1.5"/>
                  <path d="M12 8v4M12 16h.01" stroke="#ff4d4d" strokeWidth="1.5" strokeLinecap="round"/>
                </svg>
                {error}
              </div>
            )}

            <button className={`login-btn ${isLoading ? "loading" : ""}`} type="submit" disabled={isLoading}>
              {isLoading ? (
                <span className="btn-loading">
                  <span className="spinner" />
                  AUTHENTICATING...
                </span>
              ) : (
                <>
                  <svg viewBox="0 0 24 24" fill="none" width="16" height="16">
                    <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l5-5-5-5M15 12H3"
                      stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                  AUTHENTICATE
                </>
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}