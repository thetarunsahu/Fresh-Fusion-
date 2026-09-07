export function Panel({ title, eyebrow, children, className = "" }) {
  return (
    <section className={`workspacePanel ${className}`}>
      <div className="panelHeading">
        {eyebrow && <span className="eyebrow">{eyebrow}</span>}
        <h2>{title}</h2>
      </div>
      {children}
    </section>
  );
}
export function StatusChip({ tone = "neutral", children }) {
  return <span className={`statusChip ${tone}`}>{children}</span>;
}
export function Facts({ items }) {
  return (
    <dl className="facts">
      {items.map(([label, value]) => (
        <div key={label}>
          <dt>{label}</dt>
          <dd>{value ?? "Not available"}</dd>
        </div>
      ))}
    </dl>
  );
}
