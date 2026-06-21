# AI翡翠匹配系统前端 PRD V1

版本：V1.0  
端类型：移动端 H5  
设计输入：AI翡翠匹配系统 PRD 截图、`高翠网PRD.md`、backend recommendation system v4.5、API 返回结构设定（embedding + memory + rerank）  
输出范围：前端系统设计，不包含代码实现

## 1. 产品定位

AI翡翠匹配系统面向两类用户：

- 买家/游客：通过 AI 聊天输入翡翠需求，获取匹配货源，查看商品详情并提交联系意向。
- 商家：登录后发布商品、管理商品、查看客资、管理账户权限。

前端核心目标：

- 用聊天式入口降低买家找货成本。
- 将后端 recommendation system v4.5 的 `embedding + memory + rerank` 能力包装成稳定的推荐展示体验。
- 为商家提供轻量移动端后台，完成商品上架、AI 生成商品文案、客资管理和 VIP 权限转化。

## 2. 前端范围

### 2.1 本期包含

- AI聊天找货首页
- 商品详情页
- 商家登录/注册页
- 商家后台首页
- 商家个人中心
- 发布商品流程
- 商品管理
- 客资列表与客资详情
- 账户权限页
- 系统通知页

### 2.2 本期不包含

- 前端代码实现
- 支付闭环
- 站内 IM 即时沟通
- 真实鉴定结论
- 完整帮助中心与关于我们页面
- 管理后台 PC 端

## 3. 用户角色与权限

| 角色 | 登录状态 | 核心能力 | 权限限制 |
| --- | --- | --- | --- |
| 游客/买家 | 未登录 | 发送找货需求、查看推荐商品、提交联系意向 | 不进入商家后台 |
| 免费商家 | 已登录 | 发布最多 2 件商品、查看商品和客资列表 | 客户邮箱打码、发布额度有限、无完整客资查看权限 |
| VIP商家 | 已登录 | 发布最多 100 件商品、查看完整客资、较高展示权重 | 受 VIP 有效期约束 |

## 4. 页面拆解

### 4.1 P01 AI聊天找货首页

对应 PRD：一、首页  
对应截图：1. AI聊天找货首页

页面目标：

- 作为买家找货主入口。
- 支持多轮聊天输入翡翠需求。
- 展示后端推荐的 3 个优质货源卡片。
- 为商家提供入驻入口。

核心内容：

- 顶部 Logo 与标题：`AI翡翠匹配`
- 右上角：`商家入驻`
- AI欢迎语
- 三条快捷提示词
- 聊天消息流
- 推荐商品卡片区域
- 底部固定输入区

关键规则：

- 输入框 placeholder 固定为：`请输入您的翡翠需求...\n支持中文英文等多语言`
- 输入框为空时发送按钮置灰，不可点击。
- 输入框有内容后发送按钮可用，按钮文案为 `AI匹配`。
- 回车换行，不直接发送。
- 无聊天记录时始终展示 AI 欢迎语和 3 条提示词。
- 聊天记录使用 localStorage 保留，强刷新以外应保持。
- 每次有效推荐仅展示 3 张商品卡片。
- 非翡翠需求返回服务范围提示。

页面跳转：

| 触发 | 目标 |
| --- | --- |
| 点击商家入驻，商家未登录 | P03 商家登录/注册页 |
| 点击商家入驻，商家已登录 | P04 商家后台页 |
| 点击推荐商品卡片 | P02 商品详情页 |

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 发送聊天需求 | `POST /api/recommendations/chat` | 提交用户输入，获取 AI 回复、推荐结果、memory 状态 |
| 读取商品卡片详情 | `GET /api/products/{productId}` | 点击卡片后获取商品详情 |
| 商家登录态判断 | `GET /api/auth/session` | 决定商家入驻按钮跳转目标 |

### 4.2 P02 商品详情页

对应 PRD：二、商品详情页  
对应截图：2. 商品详情页

页面目标：

- 展示商品完整信息。
- 承接推荐商品点击后的详情查看。
- 让买家提交邮箱和留言，形成客资。

核心内容：

- 顶部返回与分享按钮
- 商品图片轮播
- 商品标题
- 预估售价
- 商品标签
- AI简介
- 商品详情
- 底部联系卖家表单

关键规则：

- 图片支持左右滑动，末尾继续滑动回到第一张。
- 联系卖家表单包含邮箱和留言，均必填。
- 提交后写入对应商家的客资列表和后台最近客资。
- 底部固定文案：`我们尊重您的隐私，仅用于卖家联系您`

页面跳转：

| 触发 | 目标 |
| --- | --- |
| 点击返回 | 上一页，通常为 P01 |
| 点击提交意向成功 | 当前页保留，展示提交成功反馈 |

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 商品详情加载 | `GET /api/products/{productId}` | 获取图片、标题、价格、简介、详情、标签、卖家信息 |
| 提交客资 | `POST /api/leads` | 创建买家联系意向 |

### 4.3 P03 商家登录/注册页

对应 PRD：三、商家登录注册页  
对应截图：3. 商家登录/注册页

页面目标：

- 用邮箱验证码完成商家登录或注册。

核心内容：

- 返回按钮
- Logo
- 页面标题：`商家入驻`
- 邮箱输入框
- 验证码输入框
- 获取验证码按钮
- 登录/注册按钮
- 底部权益说明
- 协议与隐私政策入口

关键规则：

- 验证码发送后展示倒计时。
- 登录/注册成功后，根据商家会员状态进入免费或 VIP 商家后台。
- 登录即表示同意平台服务协议与隐私政策。

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 发送验证码 | `POST /api/auth/send-code` | 向邮箱发送验证码 |
| 登录/注册 | `POST /api/auth/login` | 校验验证码并创建/读取商家身份 |
| 读取商家信息 | `GET /api/seller/profile` | 判断会员等级、有效期和后台跳转 |

### 4.4 P04 商家后台页

对应 PRD：四、商家后台页（VIP与免费）  
对应截图：4. 商家后台页

页面目标：

- 作为商家移动端工作台。
- 汇总商品数量、今日客资、累计客资。
- 提供发布商品、商品管理、客资列表、账户权限入口。

核心内容：

- 顶部导航栏
- VIP 标识
- 数据概览栏
- 4 个功能入口
- 最近客资列表
- 客资转化宣传区
- 底部导航栏

免费/VIP差异：

| 模块 | 免费商家 | VIP商家 |
| --- | --- | --- |
| 商品数量上限 | 2 | 100 |
| VIP标识 | 不展示 | 展示 |
| 客户邮箱 | 打码 | 完整展示 |
| 客资查看 | 受限 | 完整 |
| 发布入口 | 达限后置灰并引导升级 | 达限后提示下架部分商品 |

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 后台概览 | `GET /api/seller/dashboard` | 商品数量、今日客资、累计客资、最近客资 |
| 商家信息 | `GET /api/seller/profile` | 会员状态、商品额度、邮箱 |
| 通知计数 | `GET /api/notifications/unread-count` | 右上角通知状态 |

### 4.5 P05 商家个人中心

对应 PRD：五、商家个人中心  
对应截图：13. 个人中心页

页面目标：

- 展示商家账号信息。
- 提供账户权限、邮箱修改、通知设置、帮助、关于、退出登录入口。

核心内容：

- 顶部导航栏
- 商家信息卡片
- 账户信息折叠项
- 修改邮箱折叠项
- 通知设置折叠项
- 帮助中心
- 关于我们
- 退出登录

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 获取个人信息 | `GET /api/seller/profile` | 邮箱、会员状态、有效期 |
| 修改邮箱发送验证码 | `POST /api/auth/send-code` | 新邮箱验证码 |
| 保存邮箱 | `PATCH /api/seller/email` | 修改商家邮箱 |
| 保存通知设置 | `PATCH /api/seller/notification-settings` | 保存邮件通知开关 |
| 退出登录 | `POST /api/auth/logout` | 清除登录态 |

### 4.6 P06 发布商品 - 步骤引导页

对应 PRD：六、发布商品1  
对应截图：5. 发布商品 - 步骤引导页

页面目标：

- 引导商家上传商品图片。
- 触发 AI 识别与商品文案生成。

核心内容：

- 顶部导航栏
- 上传图片区域
- 4 步流程说明
- 发布额度提示
- 底部 `AI生成` 按钮

关键规则：

- 支持多图上传，原型为 3 个图片位。
- 免费商家 2/2 达限时按钮置灰，提示：`需升级VIP提升发布额度`
- VIP 达限时按钮置灰，提示：`请下架部分商品后再发布`
- 未上传图片时不允许 AI 生成。

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 上传图片 | `POST /api/uploads/images` | 上传商品图片并返回图片 URL/ID |
| AI识别生成 | `POST /api/products/ai-generate` | 基于图片生成标题、简介、详情、标签、预估价 |
| 发布额度 | `GET /api/seller/quota` | 判断按钮可用性 |

### 4.7 P07 发布商品 - AI生成结果页

对应 PRD：七、发布商品2  
对应截图：6. 发布商品 - AI生成结果页、7. 编辑商品信息页

页面目标：

- 展示 AI 生成结果。
- 允许商家编辑商品信息并确认发布。

核心内容：

- 图片预览轮播
- 商品标题输入
- 商品简介输入
- 商品详情输入
- 标签编辑
- 预估售价输入
- 确认发布按钮

关键规则：

- 除标签外均为可编辑输入框。
- 标签支持编辑、删除、添加。
- 未生成出的字段留空，商家可手动填写。
- 点击确认发布后进入商品管理页。

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 创建商品 | `POST /api/seller/products` | 保存并发布商品 |
| 保存草稿 | `POST /api/seller/products/drafts` | 生成后未发布时保存草稿 |
| 重新生成 | `POST /api/products/ai-generate` | 重新基于图片生成内容 |

### 4.8 P08 商品管理列表页

对应 PRD：八、商品管理  
对应截图：8. 商品管理列表页

页面目标：

- 查看并管理商家商品。
- 支持按全部、已上架、草稿、已下架筛选。

核心内容：

- 顶部导航栏
- 商品状态 tabs
- 商品列表
- 编辑按钮
- 删除按钮
- 底部发布新商品按钮

关键规则：

- 草稿：已 AI 生成但未发布。
- 已上架：发布成功且展示给买家。
- 已下架：商家主动下架。
- 删除商品需要二次确认弹窗。
- 底部按钮根据商家发布额度变化。

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 商品列表 | `GET /api/seller/products` | 获取不同状态商品 |
| 删除商品 | `DELETE /api/seller/products/{productId}` | 删除商品 |
| 商品状态统计 | `GET /api/seller/products/stats` | 获取 tabs 数量 |
| 发布额度 | `GET /api/seller/quota` | 控制底部按钮状态 |

### 4.9 P09 编辑商品页

对应 PRD：九、发布商品3  
对应截图：9. 编辑商品页

页面目标：

- 从商品管理进入后编辑已有商品。
- 支持替换图片、保存修改、上下架。

核心内容：

- 图片轮播
- 替换图片按钮
- 商品标题、简介、详情、标签、价格
- 上/下架按钮
- 保存修改按钮

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 商品详情 | `GET /api/seller/products/{productId}` | 获取待编辑商品 |
| 替换图片 | `POST /api/uploads/images` | 上传新图片 |
| 保存修改 | `PATCH /api/seller/products/{productId}` | 更新商品字段 |
| 上下架 | `PATCH /api/seller/products/{productId}/status` | 更新商品状态 |

### 4.10 P10 客资列表页

对应 PRD：十、客资列表  
对应截图：10. 客资列表页

页面目标：

- 展示商家收到的买家意向。
- 支持全部、待联系、已联系筛选。
- 对免费商家进行邮箱打码和升级引导。

核心内容：

- 顶部导航栏
- 客资状态 tabs
- 客资列表
- 免费商家底部升级按钮

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 客资列表 | `GET /api/seller/leads` | 获取客资列表 |
| 客资统计 | `GET /api/seller/leads/stats` | 获取 tabs 数量 |
| 商家权限 | `GET /api/seller/profile` | 判断是否打码 |

### 4.11 P11 客资详情页

对应 PRD：十一、客资详情  
对应截图：11. 客资详情页

页面目标：

- 展示单条客资完整信息。
- VIP 商家可复制邮箱并标记已联系。
- 免费商家引导升级。

核心内容：

- 留言时间
- 用户需求
- 关联商品
- 用户邮箱
- 商家账号
- 底部操作按钮

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 客资详情 | `GET /api/seller/leads/{leadId}` | 获取单条客资 |
| 标记已联系 | `PATCH /api/seller/leads/{leadId}/status` | 更新联系状态 |

### 4.12 P12 账户权限页

对应 PRD：十二、账户权限  
对应截图：12. 账户权限页

页面目标：

- 展示免费/VIP 权限差异。
- 引导升级或续费。

核心内容：

- 顶部导航栏
- 会员信息栏
- 当前权限表
- 升级/续费套餐
- 联系运营按钮
- 联系运营弹窗

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 账户权限 | `GET /api/seller/entitlements` | 获取会员等级、有效期、额度、权益 |
| 联系运营 | `POST /api/seller/upgrade-intent` | 提交升级/续费意向 |

### 4.13 P13 系统通知页

对应 PRD：十三、系统通知页

页面目标：

- 展示系统通知，包括新客资通知和 VIP 到期提醒。

核心内容：

- 顶部导航栏
- 通知列表
- 通知时间
- 通知内容

API依赖：

| 场景 | API | 用途 |
| --- | --- | --- |
| 通知列表 | `GET /api/notifications` | 获取通知 |
| 标记已读 | `PATCH /api/notifications/read` | 进入页面后标记已读 |

## 5. 页面与 API 依赖总览

| 页面 | 主要API |
| --- | --- |
| P01 AI聊天找货首页 | `POST /api/recommendations/chat`、`GET /api/auth/session` |
| P02 商品详情页 | `GET /api/products/{productId}`、`POST /api/leads` |
| P03 商家登录/注册页 | `POST /api/auth/send-code`、`POST /api/auth/login` |
| P04 商家后台页 | `GET /api/seller/dashboard`、`GET /api/seller/profile` |
| P05 商家个人中心 | `GET /api/seller/profile`、`PATCH /api/seller/email`、`PATCH /api/seller/notification-settings` |
| P06 发布商品步骤页 | `POST /api/uploads/images`、`POST /api/products/ai-generate`、`GET /api/seller/quota` |
| P07 发布商品结果页 | `POST /api/seller/products`、`POST /api/seller/products/drafts` |
| P08 商品管理列表页 | `GET /api/seller/products`、`DELETE /api/seller/products/{productId}` |
| P09 编辑商品页 | `GET /api/seller/products/{productId}`、`PATCH /api/seller/products/{productId}` |
| P10 客资列表页 | `GET /api/seller/leads`、`GET /api/seller/leads/stats` |
| P11 客资详情页 | `GET /api/seller/leads/{leadId}`、`PATCH /api/seller/leads/{leadId}/status` |
| P12 账户权限页 | `GET /api/seller/entitlements`、`POST /api/seller/upgrade-intent` |
| P13 系统通知页 | `GET /api/notifications`、`PATCH /api/notifications/read` |

## 6. 推荐系统对接设计

### 6.1 前端调用入口

推荐系统只由 P01 AI聊天找货首页直接调用。其他页面通过商品 ID 或客资 ID 与业务 API 交互。

推荐接口建议：

| 字段 | 说明 |
| --- | --- |
| API | `POST /api/recommendations/chat` |
| 调用方 | P01 AI聊天找货首页 |
| 请求时机 | 用户点击 `AI匹配` 或点击快捷提示词 |
| 返回用途 | 渲染 AI 文本回复、推荐商品卡片、更新会话记忆 |

### 6.2 请求数据结构

| 字段 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `sessionId` | string | 是 | 前端生成或后端返回的聊天会话 ID |
| `message` | string | 是 | 用户本轮输入 |
| `locale` | string | 否 | 用户语言，默认 `zh-CN` |
| `history` | ChatMessage[] | 否 | 本地最近若干轮聊天上下文，最终以后端 memory 为准 |
| `buyerContext` | BuyerContext | 否 | 前端可解析出的预算、品类、用途等浅层上下文 |

### 6.3 返回数据结构

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sessionId` | string | 会话 ID |
| `reply` | AssistantReply | AI 文本回复 |
| `intent` | RecommendationIntent | 后端识别出的需求意图 |
| `memory` | MemoryState | 后端会话记忆摘要 |
| `embedding` | EmbeddingMeta | 向量检索相关元信息 |
| `rerank` | RerankMeta | 重排策略与分数信息 |
| `items` | RecommendedProduct[] | 推荐商品，前端最多展示 3 个 |
| `traceId` | string | 排查问题用链路 ID |

### 6.4 embedding + memory + rerank 前端消费方式

| 后端能力 | 前端是否展示 | 前端用途 |
| --- | --- | --- |
| embedding | 默认不展示 | 用于理解推荐来自语义检索；前端只消费召回结果和 trace 信息 |
| memory | 部分展示/隐式使用 | 支持多轮对话；前端保存 sessionId，不自行实现长期记忆 |
| rerank | 默认不展示 | 前端按后端排序展示，不重新排序 |

### 6.5 推荐卡片排序规则

- 前端默认使用 `items` 返回顺序。
- 展示数量固定为 3。
- 若返回超过 3 条，仅展示前 3 条。
- 若少于 3 条，按实际数量展示，不补假数据。
- 若无推荐结果，展示 AI 文本解释和重新输入引导。

### 6.6 异常与空状态

| 场景 | 前端表现 |
| --- | --- |
| 请求中 | 显示 AI 正在匹配状态 |
| 网络失败 | 展示重试提示，保留用户输入 |
| 后端超时 | 展示“匹配时间较长，请稍后重试” |
| 非翡翠需求 | 展示固定服务范围回复 |
| 无推荐商品 | 展示 AI 解释，并引导补充预算、品类、尺寸、品相 |
| 商品已下架 | 卡片点击详情时提示商品不可用 |

## 7. 数据结构定义

### 7.1 ChatMessage

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `id` | string | 消息 ID |
| `role` | `user` / `assistant` / `system` | 消息角色 |
| `content` | string | 文本内容 |
| `createdAt` | string | ISO 时间 |
| `recommendationGroupId` | string | 推荐结果组 ID，可为空 |
| `status` | `sending` / `success` / `failed` | 消息状态 |

### 7.2 RecommendedProduct

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `productId` | string | 商品 ID |
| `sellerId` | string | 商家 ID |
| `title` | string | 商品标题 |
| `coverImageUrl` | string | 商品首图 |
| `price` | number | 预估售价，单位元 |
| `tags` | string[] | 商品标签 |
| `summary` | string | 商品简介 |
| `rankScore` | number | 后端综合排序分 |
| `matchReasons` | string[] | 匹配原因，可用于后续展示 |
| `status` | `active` / `inactive` | 商品展示状态 |

### 7.3 ProductDetail

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `productId` | string | 商品 ID |
| `sellerId` | string | 商家 ID |
| `title` | string | 商品标题 |
| `images` | ImageAsset[] | 商品图片 |
| `price` | number | 预估售价 |
| `summary` | string | 简介 |
| `detail` | string | 详情 |
| `tags` | string[] | 标签 |
| `status` | `active` / `draft` / `inactive` | 商品状态 |
| `createdAt` | string | 发布时间 |
| `updatedAt` | string | 更新时间 |

### 7.4 SellerProfile

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `sellerId` | string | 商家 ID |
| `email` | string | 商家邮箱 |
| `membership` | `free` / `vip` | 会员类型 |
| `vipStartAt` | string | VIP 开始时间，免费商家为空 |
| `vipEndAt` | string | VIP 到期时间，免费商家为空 |
| `productLimit` | number | 商品发布上限 |
| `activeProductCount` | number | 当前已发布数量 |
| `notificationSettings` | NotificationSettings | 通知设置 |

### 7.5 SellerDashboard

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `productCount` | number | 商品数量 |
| `productLimit` | number | 商品上限 |
| `todayLeadCount` | number | 今日客资 |
| `totalLeadCount` | number | 累计客资 |
| `recentLeads` | Lead[] | 最近客资 |

### 7.6 Lead

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `leadId` | string | 客资 ID |
| `sellerId` | string | 商家 ID |
| `productId` | string | 关联商品 ID |
| `productTitle` | string | 关联商品标题 |
| `productCoverImageUrl` | string | 商品首图 |
| `buyerEmail` | string | 买家邮箱，后端根据权限返回完整或打码 |
| `buyerMessage` | string | 买家留言 |
| `status` | `pending` / `contacted` | 联系状态 |
| `createdAt` | string | 留资时间 |

### 7.7 MembershipEntitlements

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `membership` | `free` / `vip` | 会员类型 |
| `productLimit` | number | 商品发布上限 |
| `todayPublishedCount` | number | 今日已发布 |
| `leadVisibility` | `masked` / `full` | 客资查看权限 |
| `priorityWeight` | `low` / `high` | 优先展示权重 |
| `plans` | VipPlan[] | 可升级/续费套餐 |

### 7.8 Notification

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `notificationId` | string | 通知 ID |
| `type` | `new_lead` / `vip_expiring` | 通知类型 |
| `content` | string | 通知内容 |
| `createdAt` | string | 通知时间 |
| `readAt` | string | 已读时间，可为空 |

## 8. UI组件拆解

### 8.1 全局组件

| 组件 | 使用页面 | 说明 |
| --- | --- | --- |
| `MobilePageShell` | 全部页面 | 移动端 H5 页面容器 |
| `TopNavBar` | P02-P13 | 顶部导航，支持返回、标题、右侧按钮 |
| `BottomTabBar` | P04、P08、P10、P12、P05 | 商家后台底部导航 |
| `PrimaryButton` | 全部表单页 | 主题绿色主按钮 |
| `IconButton` | 多页面 | 返回、分享、通知、删除等图标按钮 |
| `TagList` | 商品相关页面 | 翡翠标签展示与换行 |
| `ImageCarousel` | 商品详情、发布结果、编辑商品 | 图片轮播与页码 |
| `Toast` | 全局 | 轻提示 |
| `ConfirmDialog` | 商品删除、联系运营 | 确认弹窗 |
| `EmptyState` | 列表页 | 空列表展示 |
| `LoadingState` | AI生成、推荐、列表加载 | 加载状态 |

### 8.2 AI聊天组件

| 组件 | 说明 |
| --- | --- |
| `ChatHeader` | Logo、标题、商家入驻按钮 |
| `WelcomeMessage` | AI 欢迎语 |
| `PromptChips` | 三条快捷提示词 |
| `ChatMessageList` | 消息流容器 |
| `UserBubble` | 用户消息气泡 |
| `AssistantBubble` | AI消息气泡 |
| `RecommendationCardGroup` | 推荐商品卡片组 |
| `RecommendationCard` | 单个推荐商品 |
| `ChatInputBar` | 底部输入框与发送按钮 |

### 8.3 商品组件

| 组件 | 说明 |
| --- | --- |
| `ProductHeroCarousel` | 商品图片大图轮播 |
| `ProductPrice` | 绿色价格与“预估价” |
| `ProductSection` | 简介、详情等段落区 |
| `ContactSellerForm` | 邮箱和留言表单 |
| `ProductListItem` | 商品管理列表项 |
| `ProductStatusTabs` | 全部、已上架、草稿、已下架 |
| `ProductEditForm` | 商品编辑表单 |
| `EditableTagList` | 可编辑标签列表 |

### 8.4 商家后台组件

| 组件 | 说明 |
| --- | --- |
| `DashboardStatsPanel` | 商品数量、今日客资、累计客资 |
| `DashboardActionGrid` | 发布商品、商品管理、客资列表、账户权限 |
| `RecentLeadList` | 最近客资 |
| `MembershipBadge` | VIP 标识 |
| `QuotaHint` | 发布额度提示 |
| `AccountMenuList` | 个人中心菜单 |

### 8.5 客资组件

| 组件 | 说明 |
| --- | --- |
| `LeadTabs` | 全部、待联系、已联系 |
| `LeadListItem` | 客资列表项 |
| `LeadDetailPanel` | 客资详情字段展示 |
| `MaskedEmail` | 邮箱打码展示 |
| `UpgradeCtaBar` | 免费商家升级引导 |

### 8.6 账户与通知组件

| 组件 | 说明 |
| --- | --- |
| `EntitlementCard` | 会员信息栏 |
| `EntitlementTable` | 当前权限表 |
| `VipPlanList` | 套餐列表 |
| `NotificationListItem` | 系统通知项 |

## 9. 用户交互流程

### 9.1 买家从输入到推荐展示

1. 买家进入 P01 首页。
2. 前端读取 localStorage 中的聊天记录。
3. 如果无聊天记录，展示 AI 欢迎语与快捷提示词。
4. 买家输入需求或点击快捷提示词。
5. 前端校验输入非空，创建用户消息并追加到消息流。
6. 前端调用 `POST /api/recommendations/chat`。
7. 后端完成意图识别、memory 更新、embedding 召回和 rerank 排序。
8. 前端收到 AI 回复和推荐商品。
9. 前端追加 AI 文本消息。
10. 若返回推荐商品，前端展示 `为您找到以下优质货源` 和最多 3 张商品卡片。
11. 买家点击商品卡片进入 P02 商品详情页。
12. 买家填写邮箱和留言，提交联系意向。
13. 前端调用 `POST /api/leads`。
14. 后端将客资写入对应商家后台。
15. 商家在 P04、P10、P11 查看该客资。

### 9.2 商家入驻到后台

1. 商家在 P01 点击 `商家入驻`。
2. 前端调用会话接口判断登录态。
3. 未登录进入 P03。
4. 商家输入邮箱并获取验证码。
5. 商家输入验证码并点击登录/注册。
6. 后端返回商家身份与会员状态。
7. 前端根据 `membership` 跳转 P04。
8. 免费商家看到免费额度与打码客资；VIP 商家看到 VIP 标识和完整客资。

### 9.3 商家发布商品

1. 商家从 P04 点击 `发布商品`。
2. 前端检查 `sellerQuota`。
3. 若额度不足，按钮置灰并提示升级或下架商品。
4. 若额度充足，进入 P06。
5. 商家上传商品图片。
6. 前端上传图片，获取 imageId/imageUrl。
7. 商家点击 `AI生成`。
8. 前端调用 `POST /api/products/ai-generate`。
9. 后端返回标题、简介、详情、标签、预估价。
10. 前端进入 P07 并填充 AI 生成字段。
11. 商家编辑字段后点击确认发布。
12. 前端调用 `POST /api/seller/products`。
13. 成功后进入 P08 商品管理列表。

### 9.4 商家处理客资

1. 买家在 P02 提交联系意向。
2. 后端创建 Lead 并归属对应 sellerId。
3. 商家在 P04 最近客资中看到新记录。
4. 商家进入 P10 客资列表。
5. 免费商家看到打码邮箱，并看到升级按钮。
6. VIP 商家看到完整邮箱。
7. 商家点击客资进入 P11。
8. VIP 商家可复制邮箱并标记已联系。
9. 前端调用 `PATCH /api/seller/leads/{leadId}/status` 更新状态。

## 10. 与后端的对接方式

### 10.1 认证与会话

- 商家端使用邮箱验证码登录。
- 登录成功后后端应设置安全会话凭证。
- 前端通过 `GET /api/auth/session` 判断是否已登录。
- 未登录访问商家页面时，应跳转 P03。
- 退出登录调用 `POST /api/auth/logout` 并清除本地商家态。

### 10.2 权限控制

- 免费/VIP 权限以服务端返回为准。
- 客户邮箱是否打码应优先由后端控制，前端只按返回内容展示。
- 商品发布额度以 `GET /api/seller/quota` 或 profile/entitlements 返回为准。
- 前端仍需做交互层置灰，但不能替代后端权限校验。

### 10.3 推荐链路

- 前端只负责提交用户输入、展示结果和维护 sessionId。
- memory 长期状态以后端为准，前端 localStorage 只用于页面刷新后的聊天体验恢复。
- embedding 与 rerank 细节不由前端计算。
- 后端返回 `traceId`，前端在错误上报中携带，便于排查推荐问题。

### 10.4 商品与客资链路

- 商品创建、编辑、上下架、删除均通过商家 API。
- 买家仅能读取已上架商品详情。
- 客资创建由买家详情页触发。
- 客资读取、标记已联系由商家端 API 触发。

### 10.5 图片上传

- 前端先上传图片，获得图片资源 ID 和 URL。
- AI生成商品信息使用图片资源 ID。
- 商品保存时提交图片资源 ID 列表。
- 后端应返回可公开访问的图片 URL，用于推荐卡片、详情和商品管理展示。

### 10.6 错误处理约定

| 错误类型 | 前端处理 |
| --- | --- |
| 未登录 | 跳转 P03 |
| 无权限 | Toast 提示并引导升级 |
| 发布额度不足 | 禁用发布入口并展示额度提示 |
| 表单校验失败 | 表单内提示 |
| 推荐失败 | 聊天流中展示可重试提示 |
| 商品不存在/下架 | 展示商品不可用 |
| 图片上传失败 | 保留已选图片并允许重试 |

## 11. 路由建议

| 页面 | 路由 |
| --- | --- |
| P01 AI聊天首页 | `/` |
| P02 商品详情 | `/products/:productId` |
| P03 商家登录/注册 | `/seller/login` |
| P04 商家后台 | `/seller/dashboard` |
| P05 个人中心 | `/seller/profile` |
| P06 发布商品步骤 | `/seller/products/new` |
| P07 发布商品结果 | `/seller/products/new/review` |
| P08 商品管理 | `/seller/products` |
| P09 编辑商品 | `/seller/products/:productId/edit` |
| P10 客资列表 | `/seller/leads` |
| P11 客资详情 | `/seller/leads/:leadId` |
| P12 账户权限 | `/seller/entitlements` |
| P13 系统通知 | `/seller/notifications` |

## 12. 状态管理建议

### 12.1 本地状态

| 状态 | 存储位置 | 说明 |
| --- | --- | --- |
| 聊天输入框内容 | 页面内 state | 不需要持久化 |
| 当前聊天消息 | localStorage + 页面 state | 刷新后恢复聊天记录 |
| 推荐 sessionId | localStorage | 维持多轮推荐 |
| 图片上传临时列表 | 页面内 state | 发布商品流程内使用 |
| 商品编辑表单 | 页面内 state | 提交后以服务端为准 |

### 12.2 服务端状态

| 状态 | 来源 |
| --- | --- |
| 商家登录态 | auth session |
| 会员等级与权益 | seller profile/entitlements |
| 商品列表与状态 | seller products |
| 客资列表与状态 | seller leads |
| 通知列表 | notifications |
| 推荐记忆 | recommendation memory |

## 13. 缺失功能清单（前端视角）

### 13.1 后端接口待确认

| 缺口 | 影响 |
| --- | --- |
| recommendation system v4.5 的正式接口路径、请求字段、返回字段未提供 | P01 推荐链路只能按假设设计 |
| `embedding + memory + rerank` 返回结构未给出精确定义 | 前端无法确定 trace、score、matchReasons 是否可展示 |
| 商品 AI 生成接口未明确是否支持多图、返回耗时和失败原因 | P06/P07 loading 与错误处理需确认 |
| 客资邮箱打码由后端还是前端处理未明确 | 权限安全建议后端处理 |
| 免费/VIP 权限接口未明确 | 多页面跳转、额度展示、按钮置灰依赖该接口 |
| 系统通知接口未明确 | P13 仅能做静态结构设计 |

### 13.2 产品规则待确认

| 缺口 | 影响 |
| --- | --- |
| 商家已登录点击 `商家入驻` 时跳转 VIP 还是免费后台的规则 | 需以后端会员状态判断 |
| 首页聊天记录“强刷新”清除条件不明确 | localStorage 清除策略需确认 |
| 非翡翠需求识别由前端关键词还是后端 Agent 判断 | 建议由后端判断，前端只展示结果 |
| 买家提交意向后是否需要防重复提交 | 需要明确同邮箱同商品的限制 |
| 商品分享按钮的实际交互 | 可先使用 Web Share API 或保留按钮 |
| 帮助中心、关于我们页面是否需要落地 | 当前 PRD 要求保留点击但不跳转 |

### 13.3 视觉与资源缺口

| 缺口 | 影响 |
| --- | --- |
| Logo、Bot头像、User头像源文件未提供 | 需要设计资产或 SVG/Icon 替代 |
| 主题绿色、金色、灰色的精确色值未提供 | 需从原型提取或定义设计变量 |
| 客资宣传区底图 `Image.png` 未提供 | P04 宣传区需替代图或后续补图 |
| 商品图片样例仅为原型图 | 真实数据依赖商家上传 |

### 13.4 前端技术决策待确认

| 缺口 | 影响 |
| --- | --- |
| 前端框架未指定 | 后续实现需选择 React/Vue/其他 |
| UI 图标库未指定 | 需统一使用 lucide 或项目内图标库 |
| 路由方案未指定 | 影响页面跳转与登录守卫实现 |
| 请求库、缓存策略未指定 | 影响 API 封装和错误重试 |
| 埋点方案未指定 | 推荐点击、留资转化、商家升级路径无法统计 |

## 14. 验收标准

### 14.1 文档验收

- 页面拆解覆盖 PRD 中 13 个页面。
- 每个页面明确核心目标、关键规则、跳转关系和 API 依赖。
- 数据结构覆盖聊天、推荐商品、商品详情、商家、客资、权益、通知。
- 明确 `embedding + memory + rerank` 的前端消费方式。
- 明确缺失功能清单。

### 14.2 后续实现验收建议

- 移动端 H5 首屏与截图结构一致。
- 主要页面内容在目标手机视口内可正常阅读和操作。
- 买家从输入需求到推荐展示路径完整。
- 商家从登录到发布商品、查看客资路径完整。
- 免费/VIP 差异在商品额度、客资邮箱、账户权限上表现一致。
- 所有 API 异常均有可理解的前端反馈。

