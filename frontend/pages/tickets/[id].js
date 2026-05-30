import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';

const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function TicketDetailPage() {
  const router = useRouter();
  const { id } = router.query;

  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (!id) return;
    fetchTicket();
  }, [id]);

  async function fetchTicket() {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${apiUrl}/tickets/${id}`);
      if (!response.ok) throw new Error('Unable to load ticket');
      setTicket(await response.json());
    } catch (err) {
      setError(err.message || 'Ticket load failed');
    } finally {
      setLoading(false);
    }
  }

  async function handleProcess() {
    setProcessing(true);
    setError('');
    setMessage('');
    try {
      const response = await fetch(`${apiUrl}/tickets/${id}/process`, { method: 'POST' });
      if (!response.ok) {
        const body = await response.json();
        throw new Error(body.detail || 'Processing failed');
      }
      setTicket(await response.json());
      setMessage('Ticket was reprocessed successfully.');
    } catch (err) {
      setError(err.message || 'Processing failed');
    } finally {
      setProcessing(false);
    }
  }

  return (
    <main className="page-shell">
      <section className="hero-card">
        <h1>Ticket Details</h1>
        <p>View the ticket details and agent response, then re-run processing if needed.</p>
        <Link className="nav-link" href="/tickets">
          ← Back to tickets
        </Link>
      </section>

      {message && <div className="notice success">{message}</div>}
      {error && <div className="notice error">{error}</div>}

      {loading && <div className="notice">Loading ticket...</div>}

      {ticket && (
        <section className="section-card">
          <h2>{ticket.subject}</h2>
          <p>{ticket.description}</p>
          <div className="button-row" style={{ marginBottom: '1rem' }}>
            <button className="button" disabled={processing} onClick={handleProcess}>
              {processing ? 'Processing...' : 'Re-run agent'}
            </button>
            <span className={`status-pill status-${ticket.status}`}>{ticket.status}</span>
          </div>

          <div className="ticket-card">
            <p><strong>Priority:</strong> {ticket.priority}</p>
            <p><strong>Customer:</strong> {ticket.customer_email}</p>
            <p><strong>Category:</strong> {ticket.category || 'N/A'}</p>
            <p><strong>Escalated:</strong> {ticket.escalated ? 'Yes' : 'No'}</p>
            <p><strong>Resolved:</strong> {ticket.resolved ? 'Yes' : 'No'}</p>
          </div>

          <div className="section-card">
            <h3>Agent Response</h3>
            <pre style={{ whiteSpace: 'pre-wrap', margin: 0 }}>{ticket.ai_response || 'No AI response yet.'}</pre>
          </div>

          <div className="section-card">
            <h3>Resolution Summary</h3>
            <p>{ticket.resolution_summary || 'No summary available.'}</p>
          </div>
        </section>
      )}
    </main>
  );
}
