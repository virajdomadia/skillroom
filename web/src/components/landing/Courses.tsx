export function Courses() {
  return (
    <section className="wrap courses" id="courses">
      <h2>Courses people finish</h2>
      <p className="sub">Every course is under six hours and ends with a quiz. Preview the first lesson of any of them free.</p>
      <div className="clist">
        <a className="course" href="#" style={{'--g': 'linear-gradient(140deg,#3E6B48,#1E2A24)'} as React.CSSProperties}><div className="thumb"></div><div className="body"><h3>Figma for developers</h3><span className="by">Meera Iyer · Product designer, 8 yrs</span><div className="meta"><b>₹999</b><span>5 h 20 m · 24 lessons</span></div></div></a>
        <a className="course" href="#" style={{'--g': 'linear-gradient(140deg,#F4B183,#C97C4A)'} as React.CSSProperties}><div className="thumb"></div><div className="body"><h3>Excel for small business owners</h3><span className="by">Rohit Shah · Chartered accountant</span><div className="meta"><b>₹699</b><span>3 h 45 m · 18 lessons</span></div></div></a>
        <a className="course" href="#" style={{'--g': 'linear-gradient(140deg,#8FB39A,#3E6B48)'} as React.CSSProperties}><div className="thumb"></div><div className="body"><h3>Shoot product photos on a phone</h3><span className="by">Karan Desai · E-commerce photographer</span><div className="meta"><b>₹799</b><span>2 h 50 m · 14 lessons</span></div></div></a>
      </div>
    </section>
  );
}
