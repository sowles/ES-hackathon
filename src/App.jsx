import { useState } from "react";

const effort = [
  { name: "OKR 1 · patients +20%", count: 3 },
  { name: "OKR 2 · months of supply", count: 1 },
  { name: "OKR 3 · runway", count: 1 },
  { name: "Beside or none · Nate", count: 1 },
];

const people = [
  { name: "Nate Adler", src: "/avatars/nate.jpg", work: "Primer3 for agents. Beside OKR 1.", tag: "branch" },
  { name: "Jordan Hale", src: "/avatars/jordan.jpg", work: "New site demand, and a months-of-supply forecast.", tag: "OKR 1" },
  { name: "Owen Briggs", src: "/avatars/owen.jpg", work: "Enrollment is on the October plan. No second site.", tag: "OKR 1" },
  { name: "Sam Pell", src: "/avatars/sam.jpg", work: "Runway falls to 11 months if the site opens.", tag: "OKR 3" },
  { name: "Alex Ruiz", src: "/avatars/alex.jpg", work: "Months of supply. November still clears 3.", tag: "OKR 2" },
];

const runwayBlame = [
  "PRD: open the new trial site in November.",
  "Jordan Hale: open in November. Supply covers the added patients through Q1.",
  "Alex Ruiz: November still clears months of supply.",
  "Sam Pell: runway falls from 14 months to 11. OKR 3's floor is 12.",
  "Sentiment: 2 calls to open. 1 call that the runway miss is real.",
];

const siteBlame = [
  "PRD: open the new trial site in November.",
  "Jordan Hale: open in November. Supply covers Q1. A second site does not.",
  "Owen Briggs: enrollment is on the October plan. Do not add a second site.",
  "Alex Ruiz: hold a site only if months of supply would fall under 3. November clears.",
  "Sentiment: 2 calls to open in November. 1 call against a second site.",
];

const primerBlame = [
  "PRD: let agents run Primer3.",
  "Nate Adler: build it. Scientists stay on the trial. It does not change the site plan.",
  "Sentiment: 1 call for Primer3. Beside OKR 1, not on it.",
];

const files = [
  {
    name: "Priorities",
    added: 2,
    removed: 1,
    rows: [
      {
        left: { kind: "same", text: "Grow treated patients 20% by opening one new trial site." },
        right: { kind: "same", text: "Grow treated patients 20% by opening one new trial site." },
      },
      {
        blame: siteBlame,
        left: {
          kind: "del",
          text: "Hold the new site until months of supply stay above 3.",
          note: "Jordan, Owen, Alex",
        },
        right: {
          kind: "add",
          text: "Open the new site in November. Supply covers the added patients through Q1.",
          note: "2 /chief calls to open · 1 against a second site",
        },
      },
      {
        blame: primerBlame,
        left: null,
        right: {
          kind: "add",
          text: "Let lab agents run Primer3. People stay on the trial, not the terminal.",
          note: "Nate Adler · branch · beside OKR 1",
        },
      },
    ],
  },
  {
    name: "Performance",
    added: 1,
    removed: 1,
    rows: [
      {
        left: { kind: "same", text: "Enrollment is on the October plan." },
        right: { kind: "same", text: "Enrollment is on the October plan." },
      },
      {
        blame: runwayBlame,
        left: {
          kind: "del",
          text: "Runway is 14 months at the current burn.",
          note: "Sam Pell · current plan",
        },
        right: {
          kind: "add",
          text: "Runway is 11 months if the new site opens in November.",
          note: "Sam Pell · misses OKR 3 floor of 12",
        },
      },
    ],
  },
];

function Cell({ line, onBlame }) {
  if (!line) return <div className="cell empty" />;
  const Tag = onBlame ? "button" : "div";
  return (
    <Tag className={`cell ${line.kind}`} onClick={onBlame} type={onBlame ? "button" : undefined}>
      <code>{line.kind === "add" ? "+" : line.kind === "del" ? "−" : " "}</code>
      <span>
        {line.text}
        {line.note ? <small>{line.note}</small> : null}
      </span>
    </Tag>
  );
}

export default function App() {
  const [blame, setBlame] = useState(null);
  const [comment, setComment] = useState("");
  const [sent, setSent] = useState(false);

  function openBlame(lines) {
    setBlame(lines);
  }

  function sendComment(event) {
    event.preventDefault();
    if (!comment.trim()) return;
    setSent(true);
  }

  return (
    <main className="page">
      <header className="title">
        <p className="product">chief-brief</p>
        <h1>
          Strategy update · 28 Oct 2026
          <span className="open">Open</span>
        </h1>
        <p>For the CEO and the CPO · 5 /chief calls · 4 lines would change</p>
      </header>

      <section className="box">
        <h2>Decisions needed</h2>
        <p>
          Runway falls to 11 months under OKR 3's floor of 12. Accept the miss, or ask Sam for a burn offset?
        </p>
      </section>

      <section className="box">
        <h2>Effort by OKR</h2>
        <p className="lead">Say versus do. Where the plan points, and where the five engineers are.</p>
        {effort.map((bar) => (
          <div className="bar" key={bar.name}>
            <span>{bar.name}</span>
            <span className="track">
              <span style={{ width: `${(bar.count / 3) * 100}%` }} />
            </span>
            <strong>{bar.count}</strong>
          </div>
        ))}
      </section>

      <section className="box">
        <h2>What engineers are doing</h2>
        <ul className="people">
          {people.map((person) => (
            <li key={person.name}>
              <img src={person.src} alt="" width="40" height="40" />
              <span>
                <strong>{person.name}</strong>
                <small>{person.tag}</small>
                {person.work}
              </span>
            </li>
          ))}
        </ul>
        <p className="branch">
          Branch · Nate Adler is beside OKR 1. Nobody approved Primer3 onto the goal.
          <span className="choices">Promote to beef</span>
        </p>
      </section>

      <section className="box conflict">
        <h2>Merge conflict</h2>
        <p>Jordan Hale and Alex Ruiz are both forecasting months of supply for the new site. Alex's model already covers it.</p>
      </section>

      <p className="files-label">Diff · Priorities and Performance</p>
      {files.map((file) => (
        <article className="file" key={file.name}>
          <header>
            <strong>{file.name}</strong>
            <span className="del">−{file.removed}</span>
            <span className="add">+{file.added}</span>
          </header>
          <div className="cols">
            <span>Removed</span>
            <span>Added</span>
          </div>
          {file.rows.map((row) => (
            <div key={(row.left?.text ?? "") + (row.right?.text ?? "")}>
              <div className="row">
                <Cell line={row.left} onBlame={row.blame ? () => openBlame(row.blame) : null} />
                <Cell line={row.right} onBlame={row.blame ? () => openBlame(row.blame) : null} />
              </div>
            </div>
          ))}
        </article>
      ))}

      {blame ? (
        <section className="box">
          <h2>Blame</h2>
          <ol>
            {blame.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ol>
        </section>
      ) : (
        <p className="lead">Click a changed line to open blame.</p>
      )}

      <section className="box review">
        <h2>Review</h2>
        <p className="choices">Accept republishes the plan. The next /chief uses it.</p>
        <form onSubmit={sendComment}>
          <textarea
            value={comment}
            onChange={(event) => {
              setComment(event.target.value);
              setSent(false);
            }}
            rows={3}
            placeholder="Request changes. This comment goes to every engineer cited on the line."
          />
          <div className="actions">
            <button type="button">Accept</button>
            <button type="submit">Request changes</button>
            <button type="button">Decline</button>
          </div>
        </form>
        {sent ? (
          <p>Sent on Slack to Sam Pell, Alex Ruiz, and Jordan Hale. Their next /chief reply opens with this comment.</p>
        ) : null}
      </section>

      <section className="box">
        <h2>History</h2>
        <ul>
          <li>1 Oct 2026 · CEO accepted the current plan. Runway read 14 months.</li>
          <li>28 Oct 2026 · This brief is open. The runway line has not been accepted.</li>
        </ul>
      </section>
    </main>
  );
}
