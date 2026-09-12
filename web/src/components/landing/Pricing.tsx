export function Pricing() {
  return (
    <section className="wrap pricing" id="pricing">
      <h2>Pay per course, or once for all of them</h2>
      <p className="sub">Billed through Razorpay. Cancel the subscription any time; courses you bought stay yours.</p>
      <div className="tiers">
        <div className="tier"><h3>Single course</h3><div className="price">₹699–999</div><p>Own it forever, certificate included.</p><a className="btn btn-line" href="#courses">Pick a course</a></div>
        <div className="tier all"><h3>All-access</h3><div className="price">₹499 <small>/ month</small></div><p>Every course, every new release, one subscription.</p><a className="btn btn-moss" href="#">Start all-access</a></div>
      </div>
    </section>
  );
}
