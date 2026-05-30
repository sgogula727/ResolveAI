import Link from 'next/link';

export default function Home() {
  return (
    <main className="page-shell">
      <section className="hero-card">
        <h1>ResolveAI Dashboard</h1>
        <p>
          A lightweight frontend for managing tickets, processing them through the
          Mistral-powered backend agent, and loading knowledge base documents.
        </p>
        <div className="button-row">
          <Link className="button" href="/tickets">
            View Tickets
          </Link>
          <Link className="button secondary" href="/tickets">
            Create Ticket
          </Link>
        </div>
      </section>

      <section className="info-card">
        <h2>How it works</h2>
        <ul>
          <li>Create new support tickets from the ticket page.</li>
          <li>Tickets are automatically processed by the ResolveAI agent.</li>
          <li>Open a ticket to view the agent response and status.</li>
        </ul>
      </section>
    </main>
  );
}
