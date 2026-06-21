import { useEffect, useState } from "react";
import { api } from "../api/client";
import { MobileShell, ToastBanner, TopBar } from "../components/Layout";
import type { ToastTone } from "../types";
import { navigate } from "../utils/router";

type NotificationItem = { id: number; type: string; content: string; createdAt: string; readAt?: string };

export function NotificationsPage() {
  const [items, setItems] = useState<NotificationItem[]>([]);
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();

  useEffect(() => {
    api
      .notifications()
      .then((data) => {
        setItems(data);
        void Promise.all(data.filter((item) => !item.readAt).map((item) => api.markNotificationRead(item.id)));
      })
      .catch((error) => setNotice({ message: error instanceof Error ? error.message : "通知接口不可用", tone: "error" }));
  }, []);

  return (
    <MobileShell>
      <TopBar title="系统通知" onBack={() => navigate("seller-dashboard")} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="notification-list">
        {items.map((item) => (
          <article key={item.id}>
            <time>{formatTime(item.createdAt)}</time>
            <p>{item.content}</p>
          </article>
        ))}
        {!items.length ? <p className="empty-copy">暂无系统通知。</p> : null}
      </section>
    </MobileShell>
  );
}

function formatTime(value?: string) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}
