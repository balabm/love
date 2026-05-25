import { Component } from "react";

export default class ErrorBoundary extends Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("[ErrorBoundary]", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: 32, background: "#1a0a0a", border: "1px solid #7f1d1d", borderRadius: 12, color: "#fca5a5", textAlign: "center" }}>
          <div style={{ fontSize: 18, marginBottom: 8 }}>
            Something went wrong in {this.props.name || "this panel"}
          </div>
          <div style={{ fontSize: 12, opacity: 0.6, marginBottom: 16 }}>
            {this.state.error?.message}
          </div>
          <button
            onClick={() => window.location.reload()}
            style={{ background: "#7f1d1d", color: "#fff", border: "none", padding: "8px 20px", borderRadius: 8, cursor: "pointer" }}
          >
            Reload
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
