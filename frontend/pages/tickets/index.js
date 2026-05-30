import { useEffect, useMemo, useState } from 'react';
import Link from 'next/link';

const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function TicketsPage() {
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [form, setForm] = useState({
    customer_email: '',
    subject: '',
    description: '',
    priority: 'normal',
  });
  const [message, setMessage] = useState('');

  const statusMap = useMemo(
    () => ({
      open: 'status-open',
      resolved: 'status-resolved',
      escalated: 'status-escalated',
    }),
    []
  );

  useEffect(() => {
    fetchTickets();
  }, []);

  async function fetchTickets() {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${apiUrl}/tickets`);
      if (!response.ok) throw new Error('Unable to load tickets');
      setTickets(await response.json());
    } catch (err) {
      setError(err.message || 'Ticket fetch failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage('');
    setError('');

    try {
      const response = await fetch(`${apiUrl}/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail || 'Ticket creation failed');
      }
      const ticket = await response.json();
      setTickets((current) => [ticket, ...current]);
      setForm({ customer_email: '', subject: '', description: '', priority: 'normal' });
      setMessage('Ticket created successfully and sent to the agent.');
    } catch (err) {
      setError(err.message || 'Ticket creation failed');
    }
  }

  return (
    <main className="page-shell">
      <section className="hero-card">
        <h1>Support Tickets</h1>
        <p>Submit and review support tickets that are processed automatically by the backend agent.</p>
        <Link className="nav-link" href="/">
          ← Back to home
        </Link>
      </section>

      <section className="form-card">
        <h2>Create New Ticket</h2>
        {message && <div className="notice success">{message}</div>}
        {error && <div className="notice error">{error}</div>}
        <form onSubmit={handleSubmit}>
          <label htmlFor="customer_email">Customer Email</label>
          <input
            id="customer_email"
            type="email"
            value={form.customer_email}
            onChange={(event) => setForm({ ...form, customer_email: event.target.value })}
            required
          />

          <label htmlFor="subject">Subject</label>
          <input
            id="subject"
            type="text"
            value={form.subject}
            onChange={(event) => setForm({ ...form, subject: event.target.value })}
            required
          />

          <label htmlFor="priority">Priority</label>
          <select
            id="priority"
            value={form.priority}
            onChange={(event) => setForm({ ...form, priority: event.target.value })}
          >
            <option value="low">Low</option>
            <option value="normal">Normal</option>
            <option value="high">High</option>
          </select>

          <label htmlFor="description">Description</label>
          <textarea
            id="description"
            value={form.description}
            onChange={(event) => setForm({ ...form, description: event.target.value })}
            required
          />

          <button className="button" type="submit">Create Ticket</button>
        </form>
      </section>

      <section className="section-card">
        <h2>Recent Tickets</h2>
        {loading && <div className="notice">Loading tickets...</div>}
        {error && <div className="notice error">{error}</div>}
        {!loading && !tickets.length && <div className="notice">No tickets yet. Create one to get started.</div>}
        <div className="ticket-list">
          {tickets.map((ticket) => (
            <article key={ticket.id} className="ticket-card">
              <Link href={`/tickets/${ticket.id}`}>
                <h3>{ticket.subject}</h3>
              </Link>
              <div>
                <span className={`status-pill ${statusMap[ticket.status] || 'status-open'}`}>
                  {ticket.status}
                </span>
              </div>
              <p>{ticket.description}</p>
              <p><strong>Customer:</strong> {ticket.customer_email}</p>
              <p><strong>Priority:</strong> {ticket.priority}</p>
            </article>
          ))}
        </div>
      </section>
    </main>
  );
}
