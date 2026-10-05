import { Fragment } from 'react';
import { Link as RouterLink } from 'react-router-dom';

import {
  Box,
  Link,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';

// A small Markdown subset for the help pages: headings, paragraphs, lists, code, tables, links,
// bold and inline code. Builds React elements, never HTML, so the text can't inject markup.

const slug = (text) => text.toLowerCase().replace(/[^\p{L}\p{N}]+/gu, '-').replace(/^-|-$/g, '');

const INLINE = /(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))/g;

const inline = (text) => text.split(INLINE).filter(Boolean).map((part, index) => {
  if (part.startsWith('**')) return <strong key={index}>{part.slice(2, -2)}</strong>;
  if (part.startsWith('`')) {
    return <Box component="code" key={index} sx={{ bgcolor: 'action.hover', borderRadius: 0.5, px: 0.5 }}>{part.slice(1, -1)}</Box>;
  }
  const link = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
  if (link) {
    const [, label, target] = link;
    if (target.startsWith('/')) return <Link component={RouterLink} key={index} to={target}>{label}</Link>;
    if (/^https?:\/\//.test(target)) return <Link href={target} key={index} rel="noreferrer" target="_blank">{label}</Link>;
    return <Fragment key={index}>{label}</Fragment>;
  }
  return <Fragment key={index}>{part}</Fragment>;
});

const cells = (line) => line.trim().replace(/^\||\|$/g, '').split('|').map((cell) => cell.trim());

// Parse into blocks: { type, ... }.
const parse = (source) => {
  const lines = source.replace(/\r/g, '').split('\n');
  const blocks = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (!line.trim()) {
      i += 1;
    }
    else if (line.startsWith('```')) {
      const code = [];
      i += 1;
      while (i < lines.length && !lines[i].startsWith('```')) code.push(lines[i++]);
      i += 1;
      blocks.push({ type: 'code', text: code.join('\n') });
    }
    else if (/^#{1,3} /.test(line)) {
      const level = line.match(/^#+/)[0].length;
      const [, text, id] = line.slice(level + 1).trim().match(/^(.*?)(?:\s*\{#([\w-]+)\})?$/);
      blocks.push({ type: 'heading', level, text, id: id || slug(text) });
      i += 1;
    }
    else if (/^\s*([-*]|\d+\.) /.test(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const items = [];
      while (i < lines.length && /^\s*([-*]|\d+\.) /.test(lines[i])) {
        let item = lines[i].replace(/^\s*([-*]|\d+\.) /, '');
        i += 1;
        while (i < lines.length && /^\s{2,}\S/.test(lines[i]) && !/^\s*([-*]|\d+\.) /.test(lines[i])) {
          item += ` ${lines[i].trim()}`;
          i += 1;
        }
        items.push(item);
      }
      blocks.push({ type: 'list', ordered, items });
    }
    else if (line.trim().startsWith('|') && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1] || '')) {
      const head = cells(line);
      i += 2;
      const rows = [];
      while (i < lines.length && lines[i].trim().startsWith('|')) rows.push(cells(lines[i++]));
      blocks.push({ type: 'table', head, rows });
    }
    else {
      const text = [];
      while (i < lines.length && lines[i].trim() && !/^(#{1,3} |```|\s*([-*]|\d+\.) |\s*\|)/.test(lines[i])) {
        text.push(lines[i++].trim());
      }
      if (!text.length) {
        text.push(lines[i].trim());
        i += 1;
      }
      blocks.push({ type: 'paragraph', text: text.join(' ') });
    }
  }
  return blocks;
};

const VARIANTS = { 1: 'h5', 2: 'h6', 3: 'subtitle1' };

const Markdown = ({ source }) => parse(source).map((block, index) => {
  switch (block.type) {
    case 'heading':
      return (
        <Typography component={`h${block.level + 1}`} id={block.id} key={index}
          sx={{ fontWeight: block.level === 3 ? 600 : undefined, marginTop: index ? 3 : 0, marginBottom: 1,
            scrollMarginTop: '16px' }}
          variant={VARIANTS[block.level]}>
          {block.text}
        </Typography>
      );
    case 'code':
      return (
        <Box component="pre" key={index} sx={{ bgcolor: 'action.hover', borderRadius: 1, overflowX: 'auto',
          padding: 1.5, fontSize: '0.85rem' }}>
          <code>{block.text}</code>
        </Box>
      );
    case 'list':
      return (
        <Box component={block.ordered ? 'ol' : 'ul'} key={index} sx={{ marginY: 1, paddingLeft: 3 }}>
          {block.items.map((item, itemIndex) => (
            <Typography component="li" key={itemIndex} sx={{ marginBottom: 0.5 }} variant="body2">{inline(item)}</Typography>
          ))}
        </Box>
      );
    case 'table':
      return (
        <Box key={index} sx={{ marginY: 1, overflowX: 'auto' }}>
          <Table size="small">
            <TableHead>
              <TableRow>{block.head.map((cell, c) => <TableCell key={c}>{inline(cell)}</TableCell>)}</TableRow>
            </TableHead>
            <TableBody>
              {block.rows.map((row, r) => (
                <TableRow key={r}>{row.map((cell, c) => <TableCell key={c}>{inline(cell)}</TableCell>)}</TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      );
    default:
      return <Typography key={index} sx={{ marginBottom: 1.5 }} variant="body2">{inline(block.text)}</Typography>;
  }
});

export { parse, slug };
export default Markdown;
