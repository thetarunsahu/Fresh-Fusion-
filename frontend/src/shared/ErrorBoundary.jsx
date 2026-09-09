import React from "react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { error: null };
  }

  static getDerivedStateFromError(error) {
    return { error };
  }

  componentDidCatch(error, info) {
    console.error("FreshFusion UI error", error, info);
  }

  reset = () => {
    this.setState({ error: null });
    window.location.hash = "overview";
    window.location.reload();
  };

  render() {
    if (!this.state.error) return this.props.children;

    return (
      <main className="ffRuntimeError" role="alert">
        <section>
          <span>FRESHFUSION RECOVERY</span>
          <h1>The interface hit an unexpected error.</h1>
          <p>
            Your stored inspection data has not been deleted. Reload the workspace
            to recover the interface, then retry the last action.
          </p>
          <button onClick={this.reset}>Reload workspace</button>
          <details>
            <summary>Technical detail</summary>
            <code>{this.state.error?.message || "Unknown interface error"}</code>
          </details>
        </section>
      </main>
    );
  }
}
