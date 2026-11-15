import { Component } from "react";

// If one screen breaks, the rest of the app keeps working and the person sees what to do.
export default class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { failed: false }; }
  static getDerivedStateFromError() { return { failed: true }; }
  componentDidUpdate(prev) { if (prev.resetKey !== this.props.resetKey && this.state.failed) this.setState({ failed: false }); }
  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <div className="page"><div className="state state-error" role="alert">
        <strong>This screen hit a problem.</strong>
        <span>Your data is safe. Reload the page, or open another screen from the menu.</span>
        <button className="btn btn-ghost btn-sm" onClick={() => window.location.reload()}>Reload</button>
      </div></div>
    );
  }
}
