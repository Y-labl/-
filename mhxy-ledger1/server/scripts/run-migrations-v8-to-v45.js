/**
 * apply-schema.js 已执行 migrate-v2..v7；本脚本按序执行 v8..v45（幂等跳过由各自脚本处理）。
 */
import { spawnSync } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const serverRoot = path.join(__dirname, '..');

function main() {
  for (let n = 8; n <= 45; n += 1) {
    const script = path.join(serverRoot, 'scripts', `migrate-v${n}.js`);
    const r = spawnSync(process.execPath, [script], {
      cwd: serverRoot,
      stdio: 'inherit',
      env: process.env,
    });
    if (r.status !== 0) {
      process.exit(r.status ?? 1);
    }
  }
  console.log('migrate-v8..v45 all OK.');
}

main();
