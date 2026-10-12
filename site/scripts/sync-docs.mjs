// Copies documentation/{en,de,developers} into the Starlight content folder and adapts what GitHub shows
// differently from a documentation site: the title becomes front matter, links between pages become site
// addresses, links to files outside the documentation go to GitHub, and alert blocks become asides.

import { cpSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs';
import { dirname, join, normalize, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '../..');
const DOCS = join(ROOT, 'documentation');
const OUT = join(ROOT, 'site/src/content/docs');
const BASE = '/lauschkiste';
const GITHUB = 'https://github.com/ladidadida/lauschkiste';
const SKIP = new Set(['developers/docstring/README.md']);
const ASIDES = { NOTE: 'note', TIP: 'tip', IMPORTANT: 'caution', WARNING: 'caution', CAUTION: 'danger' };

const walk = (dir) => readdirSync(dir).flatMap((name) => {
  const path = join(dir, name);
  return statSync(path).isDirectory() ? walk(path) : [path];
});

const posix = (path) => path.split('\\').join('/');

// The address of a documentation page, or null if the file is not one. The developer pages exist in English only.
function pageUrl(file) {
  const rel = posix(relative(DOCS, file));
  const match = rel.match(/^(en|de|developers)\/(.*)\.md$/);
  if (!match || SKIP.has(rel)) return null;
  const [, tree, path] = match;
  const locale = tree === 'developers' ? 'en' : tree;
  const slug = (tree === 'developers' ? `developers/${path}` : path).replace(/(^|\/)README$/, '$1').replace(/\/$/, '');
  return `${BASE}/${locale}/${slug ? `${slug}/` : ''}`;
}

function rewrite(target, sourceFile, locale) {
  if (/^(https?:|mailto:|#|\/)/.test(target)) return target;
  const [path, anchor] = target.split('#');
  const absolute = normalize(join(dirname(sourceFile), path));
  const hash = anchor ? `#${anchor}` : '';
  const page = pageUrl(absolute);
  if (page) return page + hash;
  const rel = posix(relative(DOCS, absolute));
  if (rel.startsWith('assets/screenshots/')) return `${BASE}/screenshots/${rel.slice('assets/screenshots/'.length)}`;
  if (rel.startsWith('assets/')) return `${BASE}/${rel}`;
  const fromRoot = posix(relative(ROOT, absolute));
  if (fromRoot.startsWith('..')) return target;
  const kind = existsSync(absolute) && statSync(absolute).isDirectory() ? 'tree' : 'blob';
  return `${GITHUB}/${kind}/main/${fromRoot}${hash}`;
}

function convert(text, sourceFile, locale) {
  const lines = text.split('\n');
  let title = null;
  const out = [];
  let fenced = false;
  for (let i = 0; i < lines.length; i += 1) {
    let line = lines[i];
    if (line.startsWith('```')) fenced = !fenced;
    if (fenced || line.startsWith('```')) { out.push(line); continue; }
    if (title === null && /^# /.test(line)) { title = line.slice(2).trim(); continue; }
    const alert = line.match(/^> \[!(NOTE|TIP|IMPORTANT|WARNING|CAUTION)\]\s*$/);
    if (alert) {
      const body = [];
      while (i + 1 < lines.length && lines[i + 1].startsWith('>')) { i += 1; body.push(lines[i].replace(/^> ?/, '')); }
      out.push(`:::${ASIDES[alert[1]]}`, ...body, ':::');
      continue;
    }
    line = line.replace(/\]\(([^)\s]+)\)/g, (_, target) => `](${rewrite(target, sourceFile, locale)})`);
    line = line.replace(/(<img[^>]*\ssrc=")([^"]+)(")/g, (_, a, target, b) => `${a}${rewrite(target, sourceFile, locale)}${b}`);
    out.push(line);
  }
  return { title: title ?? 'Lauschkiste', body: out.join('\n').replace(/^\n+/, '') };
}

function emit(file, locale, outPath) {
  const { title, body } = convert(readFileSync(file, 'utf8'), file, locale);
  const target = join(OUT, outPath);
  mkdirSync(dirname(target), { recursive: true });
  writeFileSync(target, `---\ntitle: ${JSON.stringify(title)}\n---\n\n${body}`);
}

rmSync(OUT, { recursive: true, force: true });
for (const locale of ['en', 'de']) {
  for (const file of walk(join(DOCS, locale)).filter((f) => f.endsWith('.md'))) {
    const rel = posix(relative(join(DOCS, locale), file));
    emit(file, locale, `${locale}/${rel.replace(/(^|\/)README\.md$/, '$1index.md')}`);
  }
}
for (const file of walk(join(DOCS, 'developers')).filter((f) => f.endsWith('.md'))) {
  const rel = posix(relative(DOCS, file));
  if (SKIP.has(rel)) continue;
  emit(file, 'en', `en/${rel.replace(/(^|\/)README\.md$/, '$1index.md')}`);
}
const shots = join(DOCS, 'assets/screenshots');
if (existsSync(shots)) cpSync(shots, join(ROOT, 'site/public/screenshots'), { recursive: true });
console.log(`documentation synced to ${relative(ROOT, OUT)}`);
