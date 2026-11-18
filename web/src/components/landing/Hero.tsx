export function Hero() {
  return (
    <section className="wrap hero">
      <div>
        <h1>Learn a skill from someone who does it for a living</h1>
        <p className="lede">Short video courses by working professionals. Watch on any device, pick up where you left off, pass the quiz, and walk away with a certificate that has your name on it.</p>
        <div className="actions"><a className="btn btn-moss" href="#courses">Browse courses</a><a className="btn btn-line" href="#teach">Teach on Skillroom</a></div>
        <div className="creators"><div className="faces"><i style={{background: '#3E6B48'} as React.CSSProperties}></i><i style={{background: '#F4B183'} as React.CSSProperties}></i><i style={{background: '#8FB39A'} as React.CSSProperties}></i><i style={{background: '#1E2A24'} as React.CSSProperties}></i></div><span>38 creators · 112 courses · new ones every week</span></div>
      </div>

      <div className="stage">
        <div className="player" role="img" aria-label="Course player preview: Figma for developers, lesson 7, Auto layout, properly, 8:12 of 12:40 watched, three earlier lessons completed">
          <div className="video" aria-hidden="true">
            <div className="title">Figma for developers<small>Lesson 7 · Auto layout, properly</small></div>
            <div className="play" aria-hidden="true"></div>
            <div className="time">08:12 / 12:40</div>
            <div className="bar"><i></i></div>
          </div>
          <div className="chapters" aria-hidden="true">
            <div className="ch done"><span><i></i>Frames and constraints</span><small>9:10</small></div>
            <div className="ch done"><span><i></i>Components and variants</span><small>14:02</small></div>
            <div className="ch done"><span><i></i>Design tokens</span><small>11:30</small></div>
            <div className="ch now"><span><i></i>Auto layout, properly</span><small>12:40</small></div>
            <div className="ch"><span><i></i>Handoff to code</span><small>10:05</small></div>
            <div className="ch"><span><i></i>Section quiz</span><small>6 questions</small></div>
          </div>
        </div>
        <div className="cert" role="img" aria-label="Example certificate of completion: Ananya Rao, Figma for developers, September 2026">
          <div className="seal" aria-hidden="true"></div>
          <div aria-hidden="true">
            <b>Certificate of completion</b>
            <div className="name">Ananya Rao</div>
            <small>Figma for developers · Sept 2026</small>
          </div>
        </div>
      </div>
    </section>
  );
}
