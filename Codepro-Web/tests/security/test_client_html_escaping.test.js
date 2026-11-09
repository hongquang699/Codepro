const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const frontend = path.join(__dirname, '..', '..', 'frontend', 'js');
const source = file => fs.readFileSync(path.join(frontend, file), 'utf8');
const attack = '<img src=x onerror=alert(1)>';

test('ranking tables escape API text before inserting HTML', () => {
  const table = { innerHTML: '' };
  const context = {
    window: {},
    document: { getElementById: () => table }
  };
  vm.createContext(context);
  vm.runInContext(source('ranking/ranking-table.js'), context);
  context.renderRankingTable([{
    rank: 1, username: attack, school: attack, country: attack,
    badge: 'bad" onclick="alert(1)', rating: 1000, solved: 1, score: 2
  }]);
  expect(table.innerHTML).not.toContain(attack);
  expect(table.innerHTML).not.toContain('onclick="alert');
  expect(table.innerHTML).toContain('&lt;img');
  expect(context.renderProblemScoreCell({ solved: true, tries: 1, time: attack })).not.toContain(attack);
});

test('community cards escape user content and reject unsafe links', () => {
  const context = {
    window: { location: { origin: 'https://oj.example.test' } },
    document: { addEventListener: () => {} },
    URL
  };
  vm.createContext(context);
  vm.runInContext(source('community/api.js'), context);
  vm.runInContext(source('community/home.js'), context);
  const html = context.renderPostCard({
    id: '1);alert(1)//', author_username: attack, author_rank: 'bad" onclick="alert(1)',
    title: attack, content: attack, tags: [attack], created_at: '2026-10-25'
  });
  expect(html).not.toContain(attack);
  expect(html).not.toContain('onclick="handleLikePost(1);');
  expect(html).toContain('&lt;img');
  expect(context.window.communityLink('javascript:alert(1)')).toBe('');
  expect(context.window.communityLink('//evil.example/path')).toBe('');
  expect(context.window.communityLink('/profile/user')).toBe('/profile/user');
});
