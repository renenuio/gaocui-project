import { useEffect, useMemo, useRef, useState } from "react";
import { api } from "../api/client";
import { BoxIcon, PlusIcon } from "../components/Icons";
import { MobileShell, SectionTitle, SellerTabBar, ToastBanner, TopBar } from "../components/Layout";
import { formatPrice, jadeImages, withJadePresentation } from "../data/jadeCatalog";
import type { Product, ProductPayload, ProductStatus, ToastTone } from "../types";
import { navigate } from "../utils/router";

type ProductTab = "all" | ProductStatus;

function normalizeProduct(product: Product, index: number): Product {
  return {
    ...withJadePresentation(product, index),
    status: product.status || "active",
    images: product.images?.length ? product.images : [product.imageUrl || jadeImages[index % jadeImages.length]]
  };
}

function statusLabel(status?: ProductStatus) {
  if (status === "draft") return "草稿";
  if (status === "inactive") return "已下架";
  return "已上架";
}

function formatDate(value?: string) {
  if (!value) return "--";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "--";
  return date.toLocaleString("zh-CN", { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function ProductManagement() {
  const [products, setProducts] = useState<Product[]>([]);
  const [quota, setQuota] = useState({ productLimit: 0, activeProductCount: 0, remaining: 0 });
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<ProductTab>("all");
  const [deleteTarget, setDeleteTarget] = useState<Product | null>(null);

  async function load() {
    setLoading(true);
    try {
      const [items, quotaResult] = await Promise.all([api.sellerProducts(), api.sellerQuota()]);
      setProducts(items.map(normalizeProduct));
      setQuota(quotaResult);
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "商品接口不可用", tone: "error" });
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  const counts = useMemo(() => {
    return products.reduce(
      (result, product) => {
        const status = product.status || "active";
        result.all += 1;
        result[status] += 1;
        return result;
      },
      { all: 0, active: 0, draft: 0, inactive: 0 }
    );
  }, [products]);

  const filteredProducts = activeTab === "all" ? products : products.filter((product) => (product.status || "active") === activeTab);
  const canPublish = quota.remaining > 0;

  async function deleteProduct() {
    if (!deleteTarget) return;
    await api.deleteProduct(deleteTarget.id);
    setDeleteTarget(null);
    await load();
  }

  return (
    <MobileShell className="dashboard-page">
      <TopBar title="商品管理" onBack={() => navigate("seller-dashboard")} right={<button className="text-button">分享</button>} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="management-tabs">
        <button className={activeTab === "all" ? "active" : ""} onClick={() => setActiveTab("all")}>全部({counts.all})</button>
        <button className={activeTab === "active" ? "active" : ""} onClick={() => setActiveTab("active")}>已上架({counts.active})</button>
        <button className={activeTab === "draft" ? "active" : ""} onClick={() => setActiveTab("draft")}>草稿({counts.draft})</button>
        <button className={activeTab === "inactive" ? "active" : ""} onClick={() => setActiveTab("inactive")}>已下架({counts.inactive})</button>
      </section>
      <SectionTitle title={loading ? "正在读取商品" : "商品列表"} />
      <section className="product-admin-list">
        {filteredProducts.map((product) => (
          <article className="admin-product-row" key={product.id}>
            <img src={product.imageUrl || product.images?.[0] || jadeImages[0]} alt={product.name} />
            <div className="admin-product-main">
              <h3>{product.name}</h3>
              <strong>{formatPrice(product.price)}</strong>
              <p>{formatDate(product.created_at)}</p>
            </div>
            <div className="admin-product-side">
              <span className={`status-pill ${product.status || "active"}`}>{statusLabel(product.status)}</span>
              <div>
                <button onClick={() => navigate("seller-publish-review", { id: product.id, mode: "edit" })}>编辑</button>
                <button className="danger-text" onClick={() => setDeleteTarget(product)}>删除</button>
              </div>
            </div>
          </article>
        ))}
        {!filteredProducts.length ? <p className="empty-copy">当前分类暂无商品。</p> : null}
      </section>
      <button className={`floating-create ${canPublish ? "" : "muted"}`} onClick={() => (canPublish ? navigate("seller-publish") : setNotice({ message: "发布额度不足。", tone: "warning" }))}>
        <PlusIcon /> {canPublish ? "发布新商品" : "发布额度不足"}
      </button>
      {deleteTarget ? (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <section className="confirm-modal">
            <h2>确认删除商品</h2>
            <p>删除后该商品将从后端商品库移除。</p>
            <div className="modal-actions">
              <button onClick={() => setDeleteTarget(null)}>取消</button>
              <button className="danger-button" onClick={deleteProduct}>确认删除</button>
            </div>
          </section>
        </div>
      ) : null}
      <SellerTabBar active="products" />
    </MobileShell>
  );
}

export function ProductPublish() {
  const [images, setImages] = useState<string[]>([]);
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();
  const [generating, setGenerating] = useState(false);
  const fileInputs = useRef<Array<HTMLInputElement | null>>([]);

  async function handleFile(index: number, file?: File) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      try {
        const uploaded = await api.uploadSellerProductImage({ image: String(reader.result || ""), filename: file.name });
        setImages((current) => {
          const next = [...current];
          next[index] = uploaded.imageUrl;
          return next.filter(Boolean).slice(0, 3);
        });
      } catch (error) {
        setNotice({ message: error instanceof Error ? error.message : "图片上传失败", tone: "error" });
      }
    };
    reader.readAsDataURL(file);
  }

  async function generate() {
    if (!images.length) {
      setNotice({ message: "请先上传至少一张商品图片。", tone: "error" });
      return;
    }
    setGenerating(true);
    try {
      const generated = await api.generateSellerProduct({ images });
      const draft = await api.createProduct({ ...generated, images, imageUrl: images[0], status: "draft" });
      navigate("seller-publish-review", { id: draft.id, mode: "edit" });
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "AI生成失败", tone: "error" });
    } finally {
      setGenerating(false);
    }
  }

  return (
    <MobileShell>
      <TopBar title="发布商品" onBack={() => navigate("seller-dashboard")} right={<span className="ai-status">AI生成</span>} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="publish-steps flow-steps">
        <div className="step active"><BoxIcon /> <span>1. 上传商品图片</span><p>上传清晰的翡翠图片，AI将为您自动生成商品文案</p></div>
        <div className="image-upload-grid">
          {[0, 1, 2].map((index) => (
            <button className={`upload-slot ${images[index] ? "filled" : ""}`} key={index} onClick={() => fileInputs.current[index]?.click()}>
              {images[index] ? <img src={images[index]} alt={`商品图${index + 1}`} /> : <><PlusIcon /><span>添加图片</span></>}
              <input ref={(element) => { fileInputs.current[index] = element; }} type="file" accept="image/*" onChange={(event) => handleFile(index, event.target.files?.[0])} />
            </button>
          ))}
        </div>
        <div className="step"><BoxIcon /> <span>2. AI智能生成</span><p>调用后端生成商品信息</p></div>
        <div className="step"><BoxIcon /> <span>3. 编辑商品信息</span><p>可修改标题、描述、标签和价格</p></div>
        <div className="step"><BoxIcon /> <span>4. 提交发布</span><p>发布后商品将在平台展示给买家</p></div>
      </section>
      <section className="publish-footer-panel">
        <button className="primary-button" disabled={generating} onClick={generate}>{generating ? "AI生成中..." : "AI生成"}</button>
      </section>
    </MobileShell>
  );
}

export function ProductPublishReview({ id }: { id?: string | null; mode?: string | null }) {
  const [product, setProduct] = useState<Product | null>(null);
  const [imageIndex, setImageIndex] = useState(0);
  const [notice, setNotice] = useState<{ message: string; tone: ToastTone }>();
  const [submitting, setSubmitting] = useState(false);
  const replaceInput = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    api
      .sellerProducts()
      .then((items) => setProduct(items.map(normalizeProduct).find((item) => String(item.id) === String(id)) || null))
      .catch((error) => setNotice({ message: error instanceof Error ? error.message : "商品读取失败", tone: "error" }));
  }, [id]);

  function update<K extends keyof Product>(key: K, value: Product[K]) {
    setProduct((current) => (current ? { ...current, [key]: value } : current));
  }

  async function replaceImage(file?: File) {
    if (!file || !product) return;
    const reader = new FileReader();
    reader.onload = async () => {
      const uploaded = await api.uploadSellerProductImage({ image: String(reader.result || ""), filename: file.name });
      const next = [...(product.images || [])];
      next[imageIndex] = uploaded.imageUrl;
      update("images", next);
      update("imageUrl", next[0]);
    };
    reader.readAsDataURL(file);
  }

  async function save(nextStatus: ProductStatus) {
    if (!product) return;
    setSubmitting(true);
    try {
      const payload: ProductPayload = {
        name: product.name,
        description: product.description || "",
        detail: product.detail || "",
        price: product.price || "",
        category: "jade",
        tags: product.tags || [],
        images: product.images || [],
        imageUrl: product.imageUrl || product.images?.[0],
        status: nextStatus
      };
      await api.updateProduct(product.id, payload);
      navigate("seller-products");
    } catch (error) {
      setNotice({ message: error instanceof Error ? error.message : "保存失败", tone: "error" });
    } finally {
      setSubmitting(false);
    }
  }

  if (!product) {
    return (
      <MobileShell>
        <TopBar title="编辑商品" onBack={() => navigate("seller-products")} />
        <ToastBanner message={notice?.message} tone={notice?.tone} />
        <p className="loading-page">正在读取商品...</p>
      </MobileShell>
    );
  }

  const images = product.images?.length ? product.images : [product.imageUrl || jadeImages[0]];

  return (
    <MobileShell>
      <TopBar title="编辑商品" onBack={() => navigate("seller-products")} />
      <ToastBanner message={notice?.message} tone={notice?.tone} />
      <section className="review-hero">
        <img src={images[imageIndex] || jadeImages[0]} alt="商品预览" />
        <button className="replace-image" onClick={() => replaceInput.current?.click()}>替换图片</button>
        <div className="carousel-dots">{images.map((_, index) => <button key={index} className={index === imageIndex ? "active" : ""} onClick={() => setImageIndex(index)} />)}</div>
        <span>{imageIndex + 1}/{Math.max(images.length, 1)}</span>
        <input ref={replaceInput} type="file" accept="image/*" onChange={(event) => replaceImage(event.target.files?.[0])} hidden />
      </section>
      <section className="publish-form review-form">
        <label>商品标题<input value={product.name} onChange={(event) => update("name", event.target.value)} /></label>
        <label>商品简介<textarea value={product.description || ""} onChange={(event) => update("description", event.target.value)} /></label>
        <label>详情<textarea value={product.detail || ""} onChange={(event) => update("detail", event.target.value)} /></label>
        <label>标签<input value={(product.tags || []).join("，")} onChange={(event) => update("tags", event.target.value.split(/[，,]/).map((tag) => tag.trim()).filter(Boolean))} /></label>
        <label>预估售价（元）<input value={String(product.price || "")} inputMode="numeric" onChange={(event) => update("price", event.target.value)} /></label>
        <div className="split-actions">
          <button className="secondary-button" disabled={submitting} onClick={() => save(product.status === "inactive" ? "active" : "inactive")}>{product.status === "inactive" ? "上架商品" : "下架商品"}</button>
          <button className="primary-button" disabled={submitting} onClick={() => save("active")}>{submitting ? "保存中..." : "确认发布"}</button>
        </div>
      </section>
    </MobileShell>
  );
}
