import fs from 'fs';
import path from 'path';
import { spawnSync } from 'child_process';
import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config({ path: path.join(process.cwd(), '.env') });

async function main() {
  const host = process.env.MYSQL_HOST || '127.0.0.1';
  const user = process.env.MYSQL_USER || 'root';
  const password = process.env.MYSQL_PASSWORD || '';
  const database = process.env.MYSQL_DATABASE || 'mhxy_ledger';

  const conn = await mysql.createConnection({
    host,
    port: Number(process.env.MYSQL_PORT || 3306),
    user,
    password,
    multipleStatements: true,
  });

  await conn.query(
    `CREATE DATABASE IF NOT EXISTS \`${database}\` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci`
  );
  await conn.query(`USE \`${database}\``);

  const schemaPath = path.join(process.cwd(), 'db', 'schema.sql');
  const sql = fs.readFileSync(schemaPath, 'utf8');
  await conn.query(sql);

  const seedPath = path.join(process.cwd(), 'db', 'seed.sql');
  const seedSql = fs.readFileSync(seedPath, 'utf8');
  await conn.query(seedSql);

  await conn.end();

  const mig2 = spawnSync(process.execPath, [path.join(process.cwd(), 'scripts', 'migrate-v2.js')], {
    stdio: 'inherit',
    cwd: process.cwd(),
    env: process.env,
  });
  if (mig2.status !== 0) process.exit(mig2.status ?? 1);

  const mig3 = spawnSync(process.execPath, [path.join(process.cwd(), 'scripts', 'migrate-v3.js')], {
    stdio: 'inherit',
    cwd: process.cwd(),
    env: process.env,
  });
  if (mig3.status !== 0) process.exit(mig3.status ?? 1);

  const mig4 = spawnSync(process.execPath, [path.join(process.cwd(), 'scripts', 'migrate-v4.js')], {
    stdio: 'inherit',
    cwd: process.cwd(),
    env: process.env,
  });
  if (mig4.status !== 0) process.exit(mig4.status ?? 1);

  const mig5 = spawnSync(process.execPath, [path.join(process.cwd(), 'scripts', 'migrate-v5.js')], {
    stdio: 'inherit',
    cwd: process.cwd(),
    env: process.env,
  });
  if (mig5.status !== 0) process.exit(mig5.status ?? 1);

  const mig6 = spawnSync(process.execPath, [path.join(process.cwd(), 'scripts', 'migrate-v6.js')], {
    stdio: 'inherit',
    cwd: process.cwd(),
    env: process.env,
  });
  if (mig6.status !== 0) process.exit(mig6.status ?? 1);

  const mig7 = spawnSync(process.execPath, [path.join(process.cwd(), 'scripts', 'migrate-v7.js')], {
    stdio: 'inherit',
    cwd: process.cwd(),
    env: process.env,
  });
  if (mig7.status !== 0) process.exit(mig7.status ?? 1);

  console.log('Schema + seed + migrate-v2..v7 applied OK.');
  console.log('Run: npm run db:seed  （为 demo 写入物品库预设等）');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
