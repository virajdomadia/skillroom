import { AUTHOR_URL } from "@/lib/site";

export function Footer() {
  return (
    <footer className="wrap foot">
      <span>Skillroom · a portfolio project by <a href={AUTHOR_URL}>Viraj Domadia</a></span>
      <span>skillroom.virajdomadia.com</span>
    </footer>
  );
}
