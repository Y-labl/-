import mysql from 'mysql2/promise';
import dotenv from 'dotenv';

dotenv.config();

async function tableExists(conn, db, name) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.TABLES WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? LIMIT 1`,
    [db, name]
  );
  return rows.length > 0;
}

async function columnExists(conn, db, table, column) {
  const [rows] = await conn.query(
    `SELECT 1 FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? AND COLUMN_NAME = ? LIMIT 1`,
    [db, table, column]
  );
  return rows.length > 0;
}

function bizDateKey(d) {
  if (d instanceof Date) return d.toISOString().slice(0, 10);
  return String(d).slice(0, 10);
}

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

  if (!(await tableExists(conn, database, 'consumption_day_totals'))) {
    console.log('consumption_day_totals missing; run migrate-v11 first.');
    await conn.end();
    process.exit(1);
  }

  if (!(await columnExists(conn, database, 'consumption_day_totals', 'catalog_lines_json'))) {
    await conn.query(
      `ALTER TABLE consumption_day_totals
       ADD COLUMN catalog_lines_json JSON NOT NULL DEFAULT ('[]')
       COMMENT '物品消耗快照 [{catalogItemId,quantity,name}]' AFTER note`
    );
    console.log('Added consumption_day_totals.catalog_lines_json.');
  } else {
    console.log('catalog_lines_json exists, skip add column.');
  }

  if (await tableExists(conn, database, 'consumption_day_catalog_lines')) {
    const [lines] = await conn.query(
      `SELECT l.user_id AS userId, l.biz_date AS bizDate, l.character_id AS characterId,
              l.catalog_item_id AS catalogItemId, l.quantity AS quantity, c.name AS name
       FROM consumption_day_catalog_lines l
       INNER JOIN catalog_items c ON c.id = l.catalog_item_id AND c.user_id = l.user_id`
    );

    const byKey = new Map();
    for (const row of lines) {
      const bd = bizDateKey(row.bizDate);
      const k = `${row.userId}|${bd}|${row.characterId}`;
      if (!byKey.has(k)) byKey.set(k, []);
      byKey.get(k).push({
        catalogItemId: Number(row.catalogItemId),
        quantity: Math.max(1, Math.floor(Number(row.quantity))),
        name: String(row.name || ''),
      });
    }

    for (const [k, arr] of byKey) {
      const [userId, bizDate, characterId] = k.split('|');
      const json = JSON.stringify(arr);
      const [ur] = await conn.query(
        `UPDATE consumption_day_totals SET catalog_lines_json = ? 
         WHERE user_id = ? AND biz_date = ? AND character_id = ?`,
        [json, userId, bizDate, characterId]
      );
      if (ur.affectedRows === 0) {
        await conn.query(
          `INSERT INTO consumption_day_totals
           (user_id, biz_date, character_id, rmb_amount, dream_coin_w, note, catalog_lines_json)
           VALUES (?,?,?,0,0,'',?)`,
          [userId, bizDate, characterId, json]
        );
      }
    }

    await conn.query('DROP TABLE consumption_day_catalog_lines');
    console.log('Migrated consumption_day_catalog_lines into JSON and dropped old table.');
  } else {
    console.log('consumption_day_catalog_lines absent, skip data migration.');
  }

  await conn.end();
  console.log('migrate-v12 done.');
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
