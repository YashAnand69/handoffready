export default function EvidenceGraphic() {
  return (
    <svg
      className="evidence-graphic"
      viewBox="0 0 420 174"
      role="img"
      aria-label="An agreed brief and inspected files connect through human review to the final handoff"
    >
      <defs>
        <pattern
          id="desk-grid"
          width="18"
          height="18"
          patternUnits="userSpaceOnUse"
        >
          <circle cx="1" cy="1" r=".7" fill="#bdcdb4" />
        </pattern>
      </defs>
      <rect width="420" height="174" rx="12" fill="url(#desk-grid)" />
      <path
        className="evidence-path"
        d="M90 47 H162 Q174 47 174 59 V75 M90 122 H162 Q174 122 174 110 V99 M242 87 H300"
        fill="none"
        stroke="#93ab83"
        strokeWidth="1.5"
      />
      <g fill="#fffefa" stroke="#c7d3ba">
        <rect x="20" y="21" width="80" height="49" rx="7" />
        <rect x="20" y="99" width="80" height="49" rx="7" />
        <rect x="172" y="54" width="72" height="64" rx="12" />
        <rect x="300" y="45" width="98" height="86" rx="9" />
      </g>
      <g
        fill="#5c7650"
        fontFamily="system-ui,sans-serif"
        fontSize="10"
        textAnchor="middle"
      >
        <text x="60" y="50">
          AGREED BRIEF
        </text>
        <text x="60" y="128">
          ACTUAL FILES
        </text>
        <text x="208" y="101">
          YOU REVIEW
        </text>
        <text x="349" y="112">
          THE HANDOFF
        </text>
      </g>
      <circle cx="208" cy="78" r="10" fill="#e3edda" />
      <path
        d="m203 78 4 4 6-8"
        fill="none"
        stroke="#63884f"
        strokeWidth="1.5"
        strokeLinecap="round"
      />
      <g stroke="#c6d4bd" strokeWidth="2" strokeLinecap="round">
        <path d="M320 65h53M320 76h42M320 87h49" />
      </g>
      <circle
        className="evidence-signal"
        cx="269"
        cy="87"
        r="3"
        fill="#7c9a66"
      />
    </svg>
  );
}
