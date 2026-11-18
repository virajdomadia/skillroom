import { ImageResponse } from "next/og";

export const alt = "Skillroom — learn a skill from someone who does it for a living";
export const size = { width: 1200, height: 630 };
export const contentType = "image/png";

// Onest, the site's typeface. Google serves TTF to non-browser user agents, which Satori needs.
// If the fetch fails (offline build), the image still renders with the built-in fallback font.
async function onest(weight: number): Promise<ArrayBuffer | null> {
  try {
    const css = await (await fetch(`https://fonts.googleapis.com/css2?family=Onest:wght@${weight}`)).text();
    const src = css.match(/src: url\((.+?)\) format\('(?:opentype|truetype)'\)/)?.[1];
    return src ? await (await fetch(src)).arrayBuffer() : null;
  } catch {
    return null;
  }
}

export default async function Image() {
  const [bold, medium] = await Promise.all([onest(800), onest(500)]);
  const fonts = [
    ...(bold ? [{ name: "Onest", data: bold, weight: 800 as const, style: "normal" as const }] : []),
    ...(medium ? [{ name: "Onest", data: medium, weight: 500 as const, style: "normal" as const }] : []),
  ];

  return new ImageResponse(
    (
      <div style={{ width: "100%", height: "100%", display: "flex", background: "#F7F8F4", color: "#1E2A24", fontFamily: "Onest", padding: "64px 72px" }}>
        <div style={{ display: "flex", flexDirection: "column", justifyContent: "space-between", width: 600 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16, fontSize: 36, fontWeight: 800, letterSpacing: "-0.02em" }}>
            <svg width="56" height="56" viewBox="0 0 64 64"><rect width="64" height="64" rx="18" fill="#3E6B48"/><rect x="16" y="12" width="32" height="44" rx="6" fill="#CFE0D2"/><path d="M28 24 l14 10 l-14 10 z" fill="#1E2A24"/><rect x="16" y="48" width="20" height="8" fill="#F4B183"/></svg>
            Skillroom
          </div>
          <div style={{ display: "flex", fontSize: 68, fontWeight: 800, lineHeight: 1.05, letterSpacing: "-0.035em" }}>
            Learn a skill from someone who does it for a living
          </div>
          <div style={{ display: "flex", fontSize: 26, fontWeight: 500, color: "#4B5A52" }}>
            Short video courses · quizzes · certificates
          </div>
        </div>
        <div style={{ display: "flex", flex: 1, alignItems: "center", justifyContent: "flex-end" }}>
          <div style={{ display: "flex", flexDirection: "column", width: 400, background: "#fff", border: "2px solid #D8E2DA", borderRadius: 28, overflow: "hidden" }}>
            <div style={{ display: "flex", height: 240, alignItems: "center", justifyContent: "center", background: "linear-gradient(140deg,#3E6B48,#1E2A24)", position: "relative" }}>
              <div style={{ display: "flex", width: 84, height: 84, borderRadius: 42, background: "#fff", alignItems: "center", justifyContent: "center" }}>
                <svg width="34" height="38" viewBox="0 0 34 38"><path d="M4 2 L32 19 L4 36 Z" fill="#1E2A24"/></svg>
              </div>
              <div style={{ display: "flex", position: "absolute", left: 24, right: 24, bottom: 22, height: 8, borderRadius: 4, background: "rgba(255,255,255,.25)" }}>
                <div style={{ display: "flex", width: "64%", height: 8, borderRadius: 4, background: "#F4B183" }} />
              </div>
            </div>
            <div style={{ display: "flex", flexDirection: "column", padding: "22px 26px", gap: 6 }}>
              <div style={{ display: "flex", fontSize: 26, fontWeight: 800 }}>Figma for developers</div>
              <div style={{ display: "flex", fontSize: 20, fontWeight: 500, color: "#4B5A52" }}>Lesson 7 · Auto layout, properly</div>
            </div>
          </div>
        </div>
      </div>
    ),
    { ...size, fonts },
  );
}
