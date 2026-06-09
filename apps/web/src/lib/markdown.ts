import { marked } from "marked";
import DOMPurify from "dompurify";

// 流式 markdown → HTML(带简单 XSS 防护:marked 已做基本 escape)
export function md(src: string): string {
  if (!src) return "";
  marked.setOptions({ breaks: true, gfm: true });
  return DOMPurify.sanitize(marked.parse(src) as string);
}
