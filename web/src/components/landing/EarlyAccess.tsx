import { REPO_URL } from "@/lib/site";

export function EarlyAccess() {
  return (
    <section className="wrap early" id="early-access" aria-labelledby="early-title">
      <div className="early-card">
        <span className="tag">In development</span>
        <h2 id="early-title">Skillroom isn&apos;t open yet</h2>
        <p>
          Skillroom is being built as a portfolio project by Viraj Domadia. There are no accounts,
          subscriptions or creator applications yet, so signing in, all-access and teaching aren&apos;t
          available. The code is public: follow the build, or get in touch.
        </p>
        <div className="actions">
          <a className="btn btn-moss" href={REPO_URL}>Follow the build on GitHub</a>
          <a className="btn btn-line" href="https://virajdomadia.com/#contact">Contact Viraj</a>
        </div>
      </div>
    </section>
  );
}
