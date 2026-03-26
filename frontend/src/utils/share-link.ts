export function buildShareUrl(origin: string, sharePath: string): string {
  return `${origin}${sharePath}`;
}

export async function copyShareLinkToClipboard(origin: string, sharePath: string): Promise<string> {
  const url = buildShareUrl(origin, sharePath);
  await navigator.clipboard.writeText(url);
  return url;
}
