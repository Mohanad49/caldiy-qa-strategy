export interface MailpitMessage {
  ID: string;
  Subject: string;
  To: Array<{ Address: string; Name?: string }>;
  Created?: string;
}

export interface MailpitMessageDetail extends MailpitMessage {
  Text?: string;
  HTML?: string;
}

export class MailpitClient {
  constructor(private readonly baseURL = process.env.MAILPIT_URL ?? "http://127.0.0.1:8025") {}

  async waitForMessage(
    recipient: string,
    predicate: (message: MailpitMessageDetail) => boolean,
    options: { after?: Date; timeoutMs?: number } = {}
  ): Promise<MailpitMessageDetail> {
    const deadline = Date.now() + (options.timeoutMs ?? 30_000);
    let lastSubjects: string[] = [];
    while (Date.now() < deadline) {
      const messages = await this.listMessages();
      lastSubjects = messages.map((message) => message.Subject);
      for (const message of messages) {
        if (!message.To.some((address) => address.Address.toLowerCase() === recipient.toLowerCase())) continue;
        if (options.after !== undefined && message.Created !== undefined) {
          const created = new Date(message.Created);
          // Mailpit may serialize Created at lower precision than Date.now().
          // Allow a two-second boundary tolerance; the recipient remains unique.
          if (!Number.isNaN(created.valueOf()) && created.valueOf() + 2_000 < options.after.valueOf()) continue;
        }
        const detail = await this.getMessage(message.ID);
        if (predicate(detail)) return detail;
      }
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
    throw new Error(
      `Timed out waiting for Mailpit message to ${recipient}; observed subjects: ${lastSubjects.join(" | ")}`
    );
  }

  body(message: MailpitMessageDetail): string {
    return `${message.Subject}\n${message.Text ?? ""}\n${message.HTML ?? ""}`;
  }

  private async listMessages(): Promise<MailpitMessage[]> {
    const response = await fetch(`${this.baseURL}/api/v1/messages`);
    if (!response.ok) throw new Error(`Mailpit list failed with HTTP ${response.status}`);
    const payload = (await response.json()) as { messages?: MailpitMessage[] };
    return payload.messages ?? [];
  }

  private async getMessage(id: string): Promise<MailpitMessageDetail> {
    const response = await fetch(`${this.baseURL}/api/v1/message/${encodeURIComponent(id)}`);
    if (!response.ok) throw new Error(`Mailpit message ${id} failed with HTTP ${response.status}`);
    return (await response.json()) as MailpitMessageDetail;
  }
}
