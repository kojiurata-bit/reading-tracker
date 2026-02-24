"use client";

import { useState, useEffect } from "react";

export default function NearbyBookstoreMap() {
  const [mapUrl, setMapUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!navigator.geolocation) {
      setError("お使いのブラウザは位置情報に対応していません");
      setLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const { latitude, longitude } = pos.coords;
        const url = `https://maps.google.com/maps?q=書店+本屋&ll=${latitude},${longitude}&z=14&output=embed`;
        setMapUrl(url);
        setLoading(false);
      },
      () => {
        const fallbackUrl = `https://maps.google.com/maps?q=書店+本屋&z=12&output=embed`;
        setMapUrl(fallbackUrl);
        setLoading(false);
      },
      { timeout: 8000 }
    );
  }, []);

  if (error) {
    return null;
  }

  return (
    <div className="rounded-xl overflow-hidden border border-zinc-100 bg-white shadow-sm">
      <div className="px-4 py-3 border-b border-zinc-100 flex items-center gap-2">
        <span className="text-sm text-zinc-400">📍</span>
        <h2 className="text-sm font-semibold text-zinc-700">
          近くの本屋さん
        </h2>
      </div>
      {loading ? (
        <div className="h-48 flex items-center justify-center text-zinc-300 text-sm">
          位置情報を取得中...
        </div>
      ) : mapUrl ? (
        <iframe
          src={mapUrl}
          className="w-full h-48"
          style={{ border: 0 }}
          allowFullScreen
          loading="lazy"
          referrerPolicy="no-referrer-when-downgrade"
          title="近くの本屋"
        />
      ) : null}
    </div>
  );
}
