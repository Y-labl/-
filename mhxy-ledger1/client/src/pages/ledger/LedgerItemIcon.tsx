import { useEffect, useState } from 'react';
import { ledgerManifestIconUrl, ledgerPoolIconUrl, ledgerPublicItemUrl } from './ledgerIcons';

type Props = {
  iconIndex: number;
  emoji: string;
  name: string;
  iconFile?: string;
  /** 直接作为 img src（如 /mhxy-items/a.png 或 /uploads/...） */
  imageUrl?: string;
};

export function LedgerItemIcon({ iconIndex, emoji, name, iconFile, imageUrl }: Props) {
  const manifestSrc = ledgerManifestIconUrl(name);
  const directSrc = imageUrl?.trim() || null;
  const sheetSrc = iconFile?.trim() ? ledgerPublicItemUrl(iconFile.trim()) : null;
  const poolSrc = ledgerPoolIconUrl(iconIndex);

  const [failedManifest, setFailedManifest] = useState(false);
  const [failedDirect, setFailedDirect] = useState(false);
  const [failedSheet, setFailedSheet] = useState(false);
  const [failedPool, setFailedPool] = useState(false);

  useEffect(() => {
    setFailedManifest(false);
    setFailedDirect(false);
    setFailedSheet(false);
    setFailedPool(false);
  }, [name, iconIndex, manifestSrc, directSrc, sheetSrc, poolSrc]);

  if (manifestSrc && !failedManifest) {
    return (
      <img
        className="mech-icon-img"
        src={manifestSrc}
        alt={name}
        title={name}
        loading="lazy"
        decoding="async"
        onError={() => setFailedManifest(true)}
      />
    );
  }

  if (directSrc && !failedDirect) {
    return (
      <img
        className="mech-icon-img"
        src={directSrc}
        alt={name}
        title={name}
        loading="lazy"
        decoding="async"
        onError={() => setFailedDirect(true)}
      />
    );
  }

  if (sheetSrc && !failedSheet) {
    return (
      <img
        className="mech-icon-img"
        src={sheetSrc}
        alt={name}
        title={name}
        loading="lazy"
        decoding="async"
        onError={() => setFailedSheet(true)}
      />
    );
  }

  if (!failedPool) {
    return (
      <img
        className="mech-icon-img"
        src={poolSrc}
        alt={name}
        title={name}
        loading="lazy"
        decoding="async"
        onError={() => setFailedPool(true)}
      />
    );
  }

  return (
    <span className="mech-icon-fallback" aria-hidden>
      {emoji}
    </span>
  );
}
