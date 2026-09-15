import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Copy, Check } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const CodeBlock: React.FC<{ language?: string; children: React.ReactNode }> = ({
  language,
  children,
}) => {
  const [copied, setCopied] = useState(false);
  const textContent = String(children).replace(/\n$/, '');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(textContent);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code: ', err);
    }
  };

  return (
    <div className="my-3 rounded-lg overflow-hidden border border-neutral-300 dark:border-neutral-800 shadow-xs">
      <div className="flex items-center justify-between px-3 py-1.5 bg-neutral-200 dark:bg-neutral-900 text-[11px] font-mono text-neutral-700 dark:text-neutral-400 border-b border-neutral-300 dark:border-neutral-800">
        <span className="uppercase">{language || 'code'}</span>
        <button
          onClick={handleCopy}
          className="flex items-center space-x-1 px-1.5 py-0.5 rounded hover:bg-neutral-300 dark:hover:bg-neutral-800 transition-colors text-neutral-600 dark:text-neutral-300"
          title="Copy code"
        >
          {copied ? (
            <>
              <Check className="h-3 w-3 text-emerald-500" />
              <span className="text-emerald-500">Copied</span>
            </>
          ) : (
            <>
              <Copy className="h-3 w-3" />
              <span>Copy</span>
            </>
          )}
        </button>
      </div>
      <pre className="overflow-x-auto p-3.5 text-xs font-mono bg-neutral-950 text-neutral-100 dark:bg-black/95 leading-normal">
        <code>{children}</code>
      </pre>
    </div>
  );
};

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className = '' }) => {
  return (
    <div className={`markdown-body break-words text-neutral-900 dark:text-neutral-100 ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          table({ children }) {
            return (
              <div className="my-3 w-full overflow-x-auto rounded-lg border border-neutral-300 dark:border-neutral-800 shadow-xs">
                <table className="min-w-full text-left border-collapse text-xs sm:text-sm">
                  {children}
                </table>
              </div>
            );
          },
          thead({ children }) {
            return (
              <thead className="bg-neutral-100 dark:bg-neutral-900 text-neutral-900 dark:text-neutral-100 border-b border-neutral-300 dark:border-neutral-800">
                {children}
              </thead>
            );
          },
          tbody({ children }) {
            return (
              <tbody className="divide-y divide-neutral-200 dark:divide-neutral-800 bg-white dark:bg-neutral-950/60">
                {children}
              </tbody>
            );
          },
          tr({ children }) {
            return (
              <tr className="hover:bg-neutral-50/80 dark:hover:bg-neutral-900/50 transition-colors">
                {children}
              </tr>
            );
          },
          th({ children }) {
            return (
              <th className="px-3.5 py-2 font-semibold text-xs uppercase tracking-wider border-r border-neutral-200 dark:border-neutral-800 last:border-r-0">
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td className="px-3.5 py-2.5 text-neutral-800 dark:text-neutral-200 border-r border-neutral-200 dark:border-neutral-800 last:border-r-0 align-top">
                {children}
              </td>
            );
          },
          p({ children }) {
            return <p className="mb-2.5 last:mb-0 leading-relaxed">{children}</p>;
          },
          h1({ children }) {
            return (
              <h1 className="text-base sm:text-lg font-bold mt-4 mb-2 tracking-tight text-neutral-900 dark:text-white border-b border-neutral-200 dark:border-neutral-800 pb-1">
                {children}
              </h1>
            );
          },
          h2({ children }) {
            return (
              <h2 className="text-sm sm:text-base font-semibold mt-3 mb-1.5 tracking-tight text-neutral-900 dark:text-white">
                {children}
              </h2>
            );
          },
          h3({ children }) {
            return (
              <h3 className="text-xs sm:text-sm font-semibold mt-2.5 mb-1 tracking-tight text-neutral-900 dark:text-white">
                {children}
              </h3>
            );
          },
          ul({ children }) {
            return (
              <ul className="list-disc list-outside ml-4 sm:ml-5 space-y-1 my-2 text-neutral-800 dark:text-neutral-200">
                {children}
              </ul>
            );
          },
          ol({ children }) {
            return (
              <ol className="list-decimal list-outside ml-4 sm:ml-5 space-y-1 my-2 text-neutral-800 dark:text-neutral-200">
                {children}
              </ol>
            );
          },
          li({ children }) {
            return <li className="leading-relaxed">{children}</li>;
          },
          blockquote({ children }) {
            return (
              <blockquote className="border-l-3 border-blue-500 pl-3 py-1 my-2 text-neutral-600 dark:text-neutral-400 bg-blue-50/50 dark:bg-blue-950/20 rounded-r">
                {children}
              </blockquote>
            );
          },
          strong({ children }) {
            return <strong className="font-semibold text-neutral-950 dark:text-white">{children}</strong>;
          },
          a({ href, children }) {
            return (
              <a
                href={href}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 dark:text-blue-400 underline underline-offset-2 hover:text-blue-700 dark:hover:text-blue-300 font-medium"
              >
                {children}
              </a>
            );
          },
          hr() {
            return <hr className="my-4 border-neutral-200 dark:border-neutral-800" />;
          },
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const isInline = !match && !String(children).includes('\n');

            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded font-mono text-[11px] sm:text-xs bg-neutral-200/80 dark:bg-neutral-800 text-pink-600 dark:text-pink-400 border border-neutral-300/60 dark:border-neutral-700/60"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return (
              <CodeBlock language={match ? match[1] : undefined}>
                {children}
              </CodeBlock>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
