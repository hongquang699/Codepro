const http = require('node:http');
const { Queue, Worker } = require('bullmq');

const token = process.env.PROBLEM_STORAGE_INTERNAL_TOKEN;
if (!token || !process.env.REDIS_URL || !process.env.BACKEND_VALIDATE_URL) {
  throw new Error('Problem Storage queue configuration is incomplete');
}
const redis = new URL(process.env.REDIS_URL);
const connection = { host: redis.hostname, port: Number(redis.port || 6379),
  password: redis.password || undefined, db: Number(redis.pathname.slice(1) || 0),
  maxRetriesPerRequest: null };
const queue = new Queue('problem-storage-validation', { connection });
const worker = new Worker('problem-storage-validation', async job => {
  const response = await fetch(process.env.BACKEND_VALIDATE_URL, {
    method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
    body: JSON.stringify({ version_id: job.data.version_id }), signal: AbortSignal.timeout(120000)
  });
  if (!response.ok) throw new Error(`Validation returned ${response.status}`);
  return response.json();
}, { connection, concurrency: 2 });
worker.on('failed', (job, error) => console.error('Validation failed', job && job.id, error));

http.createServer(async (req, res) => {
  if (req.url !== '/enqueue' || req.method !== 'POST' ||
      req.headers.authorization !== `Bearer ${token}`) {
    res.writeHead(403).end(); return;
  }
  try {
    const chunks = [];
    let size = 0;
    for await (const chunk of req) {
      size += chunk.length;
      if (size > 1024) throw new Error('Request too large');
      chunks.push(chunk);
    }
    const { version_id } = JSON.parse(Buffer.concat(chunks).toString('utf8'));
    if (!/^[a-f0-9-]{36}$/i.test(version_id)) throw new Error('Invalid version ID');
    await queue.add('validate', { version_id }, { jobId: version_id,
      attempts: 3, backoff: { type: 'exponential', delay: 5000 },
      removeOnComplete: { age: 86400 }, removeOnFail: { age: 604800 } });
    res.writeHead(202, { 'Content-Type': 'application/json' }).end(JSON.stringify({ queued: true }));
  } catch (error) {
    res.writeHead(400).end();
  }
}).listen(3010, '0.0.0.0');
