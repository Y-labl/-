# 梦幻西游物品图标素材说明

## 网上能搜到什么（检索结论）

- **《梦幻西游》电脑版官网**（[xyq.163.com](https://xyq.163.com/)）提供图鉴、工具箱等**浏览向**资料，**没有**面向开发者的「整包物品小图标」公开下载接口；游戏内美术资源版权归网易，**不宜**由本仓库代你批量爬取或再分发。
- 部分**第三方手游**资料站（如装备/宠物图鉴页）与**电脑版**客户端在资源上**不一定一致**，且同样存在版权与链接失效问题，因此**未在代码里写死任何外链图标 URL**。
- 与你本机 **`jingshi` 截图/抠图**、或自行从客户端资源中按合规方式取得的图标，是最稳妥的来源。

## 本仓库已替你「整理」好的部分

1. **统一目录**：`client/public/mhxy-items/`
2. **整图切格（你提供的背包截图）**：`tools/slice_mhxy_item_sheet.py` + 源图备份 `tools/source/item-sheet-original.png`。  
   生成 **`sheet-fixed-01.png` … `sheet-fixed-48.png`**（左 6×8）、**`sheet-var-01.png` … `sheet-var-16.png`**（右 2×8）。  
   重新切图：`python tools/slice_mhxy_item_sheet.py <你的截图.png>`
3. **页面绑定**：`ledgerData.ts` 里日常/浮动/夜叉格使用上述 `iconFile`；**格子顺序与物品中文名是按行优先对齐的占位**，若与真实物品不符，请改 `ledgerData` 顺序或改对应 `iconFile`。
4. **可选 manifest 覆盖**：`itemIconManifest.json` 按中文名指定文件时**优先于** `iconFile`。
5. **图标池回退**：再失败则 `item-01.png` … `item-11.png`，最后 emoji。
6. **逻辑位置**：`ledgerIcons.ts`、`LedgerItemIcon.tsx`。

## 你要做的最少步骤

1. **推荐**：在 Web 里打开 **物品库**（`/app/ledger/catalog`），维护名称、单价（w）、等级、描述；图片可填 `/mhxy-items/…` 或上传得到 `/uploads/catalog/…`。记账台会读数据库里的价格。
2. 若不用数据库：准备 **PNG** 放入 `client/public/mhxy-items/`，并按 `itemIconManifest.json` 映射中文名（见上文「可选 manifest」）。
3. 新增物品（仅静态）：改 `ledgerData.ts` + `itemIconManifest.json`。

## 可选：扩图标池数量

若 `item-12.png` 等更多池文件已放入同一目录，把 `ledgerIcons.ts` 中的 `LEDGER_ICON_POOL_SIZE` 改为新的数量即可。
