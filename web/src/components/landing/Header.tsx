export function Header() {
  return (
    <header className="wrap">
      <nav className="nav" aria-label="Main">
        <a className="logo" href="#"><svg viewBox="0 0 64 64" aria-hidden="true"><rect width="64" height="64" rx="18" fill="#3E6B48"/><rect x="16" y="12" width="32" height="44" rx="6" fill="#CFE0D2"/><path d="M28 24 l14 10 l-14 10 z" fill="#1E2A24"/><rect x="16" y="48" width="20" height="8" fill="#F4B183"/></svg>Skillroom</a>
        <ul><li><a href="#courses">Courses</a></li><li><a href="#teach">Teach</a></li><li><a href="#pricing">Pricing</a></li></ul>
        <a className="btn btn-line" href="#">Sign in</a>
      </nav>
    </header>
  );
}
