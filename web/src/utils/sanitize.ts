import DOMPurify, { type Config } from 'dompurify';

/**
 * 净化邮件 HTML 正文，移除可执行脚本与高风险事件处理器，
 * 同时保留布局/排版能力（img / table / a / inline style）。
 *
 * 邮件正文是攻击者完全控制的内容（任何人都能发邮件给目标账号），
 * v-html 必须先经过这里再渲染。
 */
const DEFAULT_CONFIG: Config = {
  USE_PROFILES: { html: true },
  // 禁止任何脚本/插件加载
  FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form'],
  // 禁止表单与远程拉取行为
  FORBID_ATTR: ['srcset', 'formaction', 'autofocus'],
  // 链接默认在新标签打开
  ADD_ATTR: ['target'],
  ALLOW_DATA_ATTR: false
};

DOMPurify.addHook('afterSanitizeAttributes', (node: Element) => {
  if (node.tagName === 'A') {
    node.setAttribute('target', '_blank');
    node.setAttribute('rel', 'noopener noreferrer nofollow');
  }
  // 阻止任何残留的事件属性
  for (const attr of Array.from(node.attributes)) {
    if (attr.name.toLowerCase().startsWith('on')) {
      node.removeAttribute(attr.name);
    }
  }
});

export function sanitizeEmailHtml(raw: string | null | undefined): string {
  if (!raw) return '';
  return DOMPurify.sanitize(raw, DEFAULT_CONFIG) as unknown as string;
}
