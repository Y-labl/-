import path from 'path';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';
import { ARTIFACT_GUIDE_CONTENT_SEED } from '../src/data/artifactGuideContentSeed.js';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function main() {
  const database = process.env.MYSQL_DATABASE || 'mhxy_ledger';
  const conn = await mysql.createConnection({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD || '',
    multipleStatements: true,
  });

  await conn.query(`USE \`${database}\``);

  const entries = Object.entries(ARTIFACT_GUIDE_CONTENT_SEED || {});
  let upserts = 0;
  for (const [name, content] of entries) {
    if (!name || !content) continue;
    const [r] = await conn.query(
      `INSERT INTO artifact_guide_content (artifact_name, content_json)
       VALUES (?, CAST(? AS JSON))
       ON DUPLICATE KEY UPDATE content_json = VALUES(content_json), updated_at = CURRENT_TIMESTAMP`,
      [String(name), JSON.stringify(content)],
    );
    upserts += Number(r.affectedRows || 0) > 0 ? 1 : 0;
  }

  const [rows] = await conn.query('SELECT COUNT(*) AS cnt FROM artifact_guide_content');
  const cnt = rows?.[0]?.cnt ?? null;
  console.log(`seed-artifact-guide-content: upserts=${upserts} total=${cnt}`);

  await conn.end();
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});

