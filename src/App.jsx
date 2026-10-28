import { useEffect, useState } from "react";

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

function Avatar({ name }) {
  const letter = (name || "?").trim().charAt(0).toUpperCase();
  return (
    <span className="avatar" aria-hidden="true">
      {letter}
    </span>
  );
}

export default function App() {
  const [brief, setBrief] = useState(null);
  const [error, setError] = useState("");
  const [blame, setBlame] = useState(null);
  const [comment, setComment] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  async function load() {
    const res = await fetch(`/api/brief?t=${Date.now()}`);
    if (!res.ok) throw new Error(`brief.json ${res.status}`);
    setBrief(await res.json());
  }

  useEffect(() => {
    load().catch((err) => setError(String(err)));
  }, []);

  async function review(action) {
    if (action === "request-changes" && !comment.trim()) {
      setNotice("Request changes needs a comment.");
      return;
    }
    setBusy(true);
    setNotice("");
    try {
      const res = await fetch("/api/review", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ action, comment }),
      });
      const body = await res.json();
      if (!res.ok || !body.ok) throw new Error(body.error || res.statusText);
      await load();
      setComment("");
      setBlame(null);
      setNotice(
        action === "accept"
          ? "Accepted. The goal in beef/goals.md is the Performance column. /chief reads that goal."
          : action === "decline"
            ? "Declined. Those lines stay off the goal."
            : "Request changes logged on REVIEW.md. The goal is unchanged.",
      );
    } catch (err) {
      setNotice(String(err));
    } finally {
      setBusy(false);
    }
  }

  if (error) {
    return (
      <main className="page">
        <p>Could not load the compiled brief. Run `python3 scripts/run_morning.py` then `yarn dev`.</p>
        <p className="lead">{error}</p>
      </main>
    );
  }

  if (!brief) {
    return (
      <main className="page">
        <p className="lead">Compiling from Chief Beef…</p>
      </main>
    );
  }

  const maxEffort = Math.max(1, ...brief.effort.map((bar) => bar.count));
  const changing = brief.files.reduce((n, file) => n + file.added + file.removed, 0);

  return (
    <main className="page">
      <header className="title">
        <p className="product">chief-brief</p>
        <h1>
          {brief.title} · {brief.date}
          <span className="open">{brief.status}</span>
        </h1>
        <p>
          Compiled from Chief Beef · Helen {brief.context.events} events / {brief.context.emails} emails ·{" "}
          {brief.context.coupled} coupled · {brief.chiefCalls} /chief calls · {changing} lines would change
        </p>
      </header>

      <section className="box">
        <h2>Decisions needed</h2>
        {brief.decisions.length ? (
          brief.decisions.map((item) => <p key={item}>{item}</p>)
        ) : (
          <p className="lead">Nothing blocked on the CEO or the CPO from this snapshot.</p>
        )}
      </section>

      <section className="box">
        <h2>Effort by OKR</h2>
        <p className="lead">Say versus do. Helen inflow coupled to the goal, plus unclassified.</p>
        {brief.effort.map((bar) => (
          <div className="bar" key={bar.name}>
            <span>{bar.name}</span>
            <span className="track">
              <span style={{ width: `${(bar.count / maxEffort) * 100}%` }} />
            </span>
            <strong>{bar.count}</strong>
          </div>
        ))}
      </section>

      <section className="box">
        <h2>What people are doing</h2>
        <ul className="people">
          {brief.people.map((person) => (
            <li key={person.name}>
              <Avatar name={person.name} />
              <span>
                <strong>{person.name}</strong>
                <small>
                  {person.tag} · {person.count} items
                </small>
                {person.work}
              </span>
            </li>
          ))}
        </ul>
        {brief.branches.map((line) => (
          <p className="branch" key={line}>
            {line}
            <span className="choices">Promote to beef is Accept on the Performance column.</span>
          </p>
        ))}
      </section>

      {brief.conflicts.map((text) => (
        <section className="box conflict" key={text}>
          <h2>Merge conflict</h2>
          <p>{text}</p>
        </section>
      ))}

      <p className="files-label">Diff · Priorities (goal) and Performance (Helen)</p>
      {brief.files.map((file) => (
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
          {file.rows.map((row, i) => (
            <div key={i}>
              <div className="row">
                <Cell line={row.left} onBlame={row.blame?.length ? () => setBlame(row.blame) : null} />
                <Cell line={row.right} onBlame={row.blame?.length ? () => setBlame(row.blame) : null} />
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
        <p className="lead">Click a changed line to open blame from Helen evidence ids.</p>
      )}

      <section className="box review">
        <h2>Review</h2>
        <p className="choices">Accept writes Performance into beef/goals.md. The next /chief uses that goal. Request changes and Decline leave the goal as it is.</p>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            review("request-changes");
          }}
        >
          <textarea
            value={comment}
            onChange={(event) => setComment(event.target.value)}
            rows={3}
            placeholder="Request changes. Logged on briefs/REVIEW.md."
          />
          <div className="actions">
            <button type="button" disabled={busy} onClick={() => review("accept")}>
              Accept
            </button>
            <button type="submit" disabled={busy}>
              Request changes
            </button>
            <button type="button" disabled={busy} onClick={() => review("decline")}>
              Decline
            </button>
          </div>
        </form>
        {notice ? <p>{notice}</p> : null}
      </section>

      <section className="box">
        <h2>History</h2>
        <ul>
          {brief.history.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>
    </main>
  );
}
