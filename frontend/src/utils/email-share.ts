export interface EmailShareDraft {
  subject: string;
  body: string;
  recipients: string[];
  href: string;
}

export interface BuildEmailShareDraftArgs {
  title: string;
  summaryLines: string[];
  shareLink: string;
  recipientEmails: string[];
}

function dedupeEmails(emails: string[]): string[] {
  return [...new Set(emails.map((email) => email.trim()).filter(Boolean))];
}

export function buildEmailShareDraft(args: BuildEmailShareDraftArgs): EmailShareDraft {
  const recipients = dedupeEmails(args.recipientEmails);
  const summaryText = args.summaryLines.length > 0 ? args.summaryLines.join("\n") : "暂无摘要内容";
  const subject = `【SmartMeeting】${args.title} 会议纪要`;
  const body = [
    `会议标题：${args.title}`,
    "",
    summaryText,
    "",
    `查看链接：${args.shareLink}`,
    "",
    "请先登录后查看。",
  ].join("\n");

  return {
    subject,
    body,
    recipients,
    href: `mailto:${recipients.join(",")}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`,
  };
}

export function openEmailShareDraft(draft: EmailShareDraft): void {
  window.location.href = draft.href;
}
