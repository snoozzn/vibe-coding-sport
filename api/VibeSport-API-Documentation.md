# VibeSport API 文档

> **版本**: v1.0.0  
> **协议**: HTTP/1.1 REST  
> **Base URL**: `http://localhost:8000/api`  
> **认证方式**: Bearer Token (JWT)  
> **日期格式**: `YYYY-MM-DD` (ISO 8601 date)  
> **内容类型**: `application/json; charset=utf-8`  
> **最后更新**: 2026-07-17  

---

## 目录

1. [概述](#1-概述)
2. [认证](#2-认证-api-auth)
3. [跑步记录](#3-跑步记录-api-running)
4. [健身记录](#4-健身记录-api-fitness)
5. [体重记录](#5-体重记录-api-weight)
6. [运动类型](#6-运动类型-api-exercise-types)
7. [仪表盘](#7-仪表盘-api-dashboard)
8. [健康检查](#8-健康检查-api-health)
9. [全局规范](#9-全局规范)
10. [前端页面 ↔ API 映射](#10-前端页面--api-映射)

---

## 1. 概述

### 1.1 设计原则

- **RESTful**: 资源导向 URL，语义化 HTTP 方法
- **JWT 认证**: 无状态 Bearer Token，24 小时过期
- **统一分页**: 列表接口统一返回 `PaginatedResponse`
- **业务校验前置**: 非法数据在 Pydantic 层即被拦截 (422)
- **密码安全**: bcrypt 哈希存储，不可逆

### 1.2 通用响应结构

#### 成功 — 单条数据
```json
{
  "field1": "value1",
  "field2": 123
}
```

#### 成功 — 分页列表
```json
{
  "items": [ ... ],
  "total": 42,
  "page": 1,
  "page_size": 20
}
```

#### 成功 — 操作确认
```json
{
  "message": "记录已删除"
}
```

#### 错误
```json
{
  "detail": "人类可读的错误描述"
}
```

### 1.3 通用 HTTP 状态码

| 状态码 | 含义 | 触发场景 |
|--------|------|----------|
| `200` | 成功 | GET, PATCH, DELETE 成功 |
| `201` | 已创建 | POST 新建资源成功 |
| `400` | 请求错误 | 业务规则冲突（如密码错误） |
| `401` | 未认证 | Token 无效/过期 |
| `403` | 无权限 | 缺少 Authorization 头 |
| `404` | 未找到 | 资源不存在或无权限访问 |
| `409` | 冲突 | 用户名/邮箱已存在 |
| `422` | 校验失败 | 请求体格式不符合 Schema |

---

## 2. 认证 (`/api/auth`)

认证模块涵盖 **注册、登录、个人信息、密码管理**，对应 PRD 功能编号 F-01 至 F-04。

### 2.1 用户注册

```http
POST /api/auth/register
```

> **PRD 映射**: F-01（用户注册）  
> **前端页面**: 注册页 (`register.html`)  

**请求体** (JSON):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | `string` | ✓ | 用户名，2-20 字符，支持中英文、数字、下划线 |
| `email` | `string` | ✓ | 邮箱地址，格式校验 |
| `password` | `string` | ✓ | 密码，8-128 字符，必须包含字母和数字 |

**请求示例**:
```json
{
  "username": "paozheajie",
  "email": "ajie@example.com",
  "password": "run12345"
}
```

**成功响应** `201 Created`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "b558d406-4ca6-4883-ad1c-42767a1bf9ae",
  "username": "paozheajie"
}
```

> **说明**: 注册成功后自动签发 JWT（免去注册后再登录），Token 有效期 24 小时。

**错误响应**:
| 状态码 | detail | 触发条件 |
|--------|--------|----------|
| `409` | `该邮箱已被注册` | 邮箱重复 |
| `409` | `该用户名已被占用` | 用户名重复 |
| `422` | `密码必须包含至少一个字母` | 密码不含字母 |
| `422` | `密码必须包含至少一个数字` | 密码不含数字 |

---

### 2.2 用户登录

```http
POST /api/auth/login
```

> **PRD 映射**: F-02（用户登录）  
> **前端页面**: 登录页 (`login.html`)  

**请求体** (JSON):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | `string` | ✓ | 注册邮箱 |
| `password` | `string` | ✓ | 明文密码 |

**请求示例**:
```json
{
  "email": "ajie@example.com",
  "password": "run12345"
}
```

**成功响应** `200 OK`:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "user_id": "b558d406-4ca6-4883-ad1c-42767a1bf9ae",
  "username": "paozheajie"
}
```

**业务规则 — 登录锁定 (PRD F-01)**:
- 连续登录失败 ≥ 5 次 → 账号锁定 **15 分钟**
- 锁定期间返回: `"账号已锁定，请 N 分钟后重试"`
- 登录成功后自动清零失败计数并解除锁定

**错误响应**:
| 状态码 | detail | 触发场景 |
|--------|--------|----------|
| `401` | `邮箱或密码错误` | 凭据不匹配或用户不存在 |
| `401` | `账号已锁定，请 N 分钟后重试` | 超过失败次数上限 |

---

### 2.3 获取当前用户信息

```http
GET /api/auth/me
```

> **PRD 映射**: F-04（个人信息管理）  
> **前端页面**: 个人中心 (`profile.html`)  

**认证**: 需要 `Authorization: Bearer <token>`

**成功响应** `200 OK`:
```json
{
  "user_id": "b558d406-4ca6-4883-ad1c-42767a1bf9ae",
  "username": "paozheajie",
  "email": "ajie@example.com",
  "avatar_url": null,
  "target_weight_kg": "65.0",
  "created_at": "2026-07-17T10:30:00"
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `user_id` | `string` | UUID v4 |
| `username` | `string` | 用户名 |
| `email` | `string` | 邮箱地址 |
| `avatar_url` | `string\|null` | 头像链接 |
| `target_weight_kg` | `string\|null` | 目标体重 (kg)，可为空 |
| `created_at` | `datetime` | 注册时间 |

---

### 2.4 更新个人信息

```http
PATCH /api/auth/me
```

> **PRD 映射**: F-04（个人信息管理）  
> **前端页面**: 个人中心 (`profile.html`)  

**认证**: 需要 `Authorization: Bearer <token>`

**请求体** (JSON, 所有字段可选):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `username` | `string` | × | 新用户名，2-20 字符 |
| `avatar_url` | `string` | × | 头像链接，≤500 字符 |
| `target_weight_kg` | `decimal` | × | 目标体重，20-500 kg |

**请求示例**:
```json
{
  "target_weight_kg": 65.0
}
```

**成功响应** `200 OK`: 返回完整 `UserOut` 对象（结构同 [2.3](#23-获取当前用户信息)）。

**错误响应**:
| 状态码 | detail | 触发场景 |
|--------|--------|----------|
| `409` | `该用户名已被占用` | 用户名重复 |

---

### 2.5 修改密码

```http
POST /api/auth/change-password
```

> **前端页面**: 个人中心 (`profile.html`)  

**认证**: 需要 `Authorization: Bearer <token>`

**请求体** (JSON):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `old_password` | `string` | ✓ | 原密码，≥8 字符 |
| `new_password` | `string` | ✓ | 新密码，≥8 字符，必须含字母和数字 |

**请求示例**:
```json
{
  "old_password": "run12345",
  "new_password": "run54321"
}
```

**成功响应** `200 OK`:
```json
{
  "message": "密码已更新"
}
```

**错误响应**:
| 状态码 | detail | 触发场景 |
|--------|--------|----------|
| `400` | `原密码错误` | 旧密码不匹配 |

---

## 3. 跑步记录 (`/api/running`)

跑步记录模块涵盖 **创建、查询、编辑、删除、统计分析**，对应 PRD 功能编号 F-05 至 F-08, F-18, F-21。

**业务规则** (PRD §2.2.1):
- 距离范围: **0.1 km ~ 100 km**，支持一位小数
- 日期**不能是未来日期**
- 同一天可录入多条跑步记录

### 3.1 录入跑步记录

```http
POST /api/running
```

> **PRD 映射**: F-05, F-06, F-07  
> **前端页面**: 跑步记录 (`running.html`)  

**认证**: 需要

**请求体** (JSON):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `distance_km` | `decimal` | ✓ | 跑步距离 (km)，0.1-100 |
| `log_date` | `date` | × | 运动日期，默认当天 |
| `notes` | `string` | × | 备注，≤2000 字符 |

**请求示例**:
```json
{
  "distance_km": 5.2,
  "log_date": "2026-07-17",
  "notes": "晨跑 天气好"
}
```

**成功响应** `201 Created`:
```json
{
  "log_id": "e2e7b0ca-2a62-404b-9f2d-afa50c042a5b",
  "user_id": "b558d406-4ca6-4883-ad1c-42767a1bf9ae",
  "distance_km": "5.2",
  "log_date": "2026-07-17",
  "notes": "晨跑 天气好",
  "created_at": "2026-07-17T10:35:00"
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `log_id` | `string` | 记录 UUID v4 |
| `user_id` | `string` | 所属用户 UUID |
| `distance_km` | `string` | 跑步距离 (Decimal 序列化为 string) |
| `log_date` | `date` | 运动日期 |
| `notes` | `string\|null` | 备注 |
| `created_at` | `datetime` | 创建时间 |

**错误响应**:
| 状态码 | 说明 | 触发场景 |
|--------|------|----------|
| `422` | `日期不能是未来日期` | `log_date` > 今天 |
| `422` | `Input should be less than or equal to 100` | `distance_km` > 100 |
| `422` | `Input should be greater than 0` | `distance_km` ≤ 0 |

---

### 3.2 查询跑步记录列表

```http
GET /api/running
```

> **PRD 映射**: F-21（历史记录列表）  
> **前端页面**: 跑步记录 (`running.html`)、统计分析 (`analytics.html`)  

**认证**: 需要

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | `int` | `1` | 页码，≥1 |
| `page_size` | `int` | `20` | 每页条数，1-100 |
| `start_date` | `date` | — | 查询起始日期 |
| `end_date` | `date` | — | 查询截止日期 |

**请求示例**:
```
GET /api/running?page=1&page_size=10&start_date=2026-07-01&end_date=2026-07-31
```

**成功响应** `200 OK`:
```json
{
  "items": [
    {
      "log_id": "e2e7b0ca-2a62-404b-9f2d-afa50c042a5b",
      "user_id": "b558d406-4ca6-4883-ad1c-42767a1bf9ae",
      "distance_km": "5.2",
      "log_date": "2026-07-17",
      "notes": "晨跑 天气好",
      "created_at": "2026-07-17T10:35:00"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

> **排序**: 按 `log_date DESC, created_at DESC` 排序（最新在前）。

---

### 3.3 查询跑步统计

```http
GET /api/running/stats
```

> **PRD 映射**: F-18（跑步日/周/月跑量汇总）  
> **前端页面**: 统计分析 (`analytics.html`)、仪表盘 (`dashboard.html`)  

**认证**: 需要

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `period` | `string` | `"week"` | 统计周期: `week` 或 `month` |

**请求示例**:
```
GET /api/running/stats?period=week
```

**成功响应** `200 OK`:
```json
{
  "total_km": 25.2,
  "avg_km": 5.0,
  "count": 5,
  "previous_total_km": 20.0,
  "trend_pct": 26.0
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `total_km` | `float` | 本周/本月累计跑量 |
| `avg_km` | `float` | 本周/本月平均单次跑量 |
| `count` | `int` | 本周/本月跑步次数 |
| `previous_total_km` | `float` | 上周/上月跑量 |
| `trend_pct` | `float\|null` | 与上一周期的趋势对比百分比（正=增长，负=下降，null=无上周数据） |

> **周期定义**:
> - `week`: 本周一至今天 vs 上周一至上周日
> - `month`: 本月 1 日至今天 vs 上月 1 日至上月最后一天

---

### 3.4 查询单条跑步记录

```http
GET /api/running/{log_id}
```

**认证**: 需要

**成功响应** `200 OK`: 返回 `RunningLogOut` 对象（结构同 [3.1](#31-录入跑步记录)）。

**错误**: `404` — 记录不存在（或不属于当前用户）。

---

### 3.5 编辑跑步记录

```http
PATCH /api/running/{log_id}
```

> **PRD 映射**: F-08（编辑记录）  
> **前端页面**: 跑步记录 (`running.html`)  

**认证**: 需要

**请求体** (JSON, 所有字段可选):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `distance_km` | `decimal` | × | 修改后的距离 |
| `log_date` | `date` | × | 修改后的日期 |
| `notes` | `string` | × | 修改后的备注 |

**请求示例**:
```json
{
  "distance_km": 6.0
}
```

**成功响应** `200 OK`: 返回更新后的 `RunningLogOut` 对象。

---

### 3.6 删除跑步记录

```http
DELETE /api/running/{log_id}
```

> **PRD 映射**: F-08（删除记录）  

**认证**: 需要

**成功响应** `200 OK`:
```json
{
  "message": "记录已删除"
}
```

---

## 4. 健身记录 (`/api/fitness`)

健身记录模块涵盖 **创建、查询、编辑、删除、频率统计**，对应 PRD 功能编号 F-09 至 F-13, F-19, F-21。

**业务规则** (PRD §2.2.2):
- 时长范围: **1 分钟 ~ 480 分钟**（8 小时）
- `duration_minutes` 和 `reps_sets` **至少填写一项**
- 预设 15 种运动类型（跑步、游泳、骑行、瑜伽、力量训练、俯卧撑、深蹲、引体向上、跳绳、普拉提、拳击、篮球、足球、羽毛球、乒乓球）

### 4.1 录入健身记录

```http
POST /api/fitness
```

> **PRD 映射**: F-09, F-10, F-11  
> **前端页面**: 健身记录 (`fitness.html`)  

**认证**: 需要

**请求体** (JSON):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `exercise_type` | `string` | ✓ | 运动类型名称，1-100 字符 |
| `duration_minutes` | `int` | 条件必填¹ | 训练时长，1-480 |
| `reps_sets` | `string` | 条件必填¹ | 组数×次数，如 `"4×12"` |
| `log_date` | `date` | × | 运动日期，默认当天 |
| `notes` | `string` | × | 备注，≤2000 字符 |

> ¹ `duration_minutes` 和 `reps_sets` 至少填写一项。

**请求示例 1 — 有氧运动（填时长）**:
```json
{
  "exercise_type": "游泳",
  "duration_minutes": 45,
  "log_date": "2026-07-17",
  "notes": "蛙泳 1km"
}
```

**请求示例 2 — 力量训练（填组数）**:
```json
{
  "exercise_type": "深蹲",
  "reps_sets": "4×12",
  "log_date": "2026-07-17"
}
```

**成功响应** `201 Created`:
```json
{
  "fitness_id": "c1a2b3d4-...",
  "user_id": "b558d406-...",
  "exercise_type": "深蹲",
  "duration_minutes": null,
  "reps_sets": "4×12",
  "log_date": "2026-07-17",
  "notes": null,
  "created_at": "2026-07-17T11:00:00"
}
```

**错误响应**:
| 状态码 | detail | 触发场景 |
|--------|--------|----------|
| `400` | `duration_minutes 和 reps_sets 至少填写一项` | 两项都为空 |
| `422` | `日期不能是未来日期` | `log_date` > 今天 |

---

### 4.2 查询健身记录列表

```http
GET /api/fitness
```

> **PRD 映射**: F-21（历史记录列表）  

**认证**: 需要

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `page` | `int` | `1` | 页码 |
| `page_size` | `int` | `20` | 每页条数 |
| `start_date` | `date` | — | 起始日期 |
| `end_date` | `date` | — | 截止日期 |
| `exercise_type` | `string` | — | 按运动类型筛选 |

**请求示例**:
```
GET /api/fitness?page=1&start_date=2026-07-01&exercise_type=深蹲
```

**成功响应** `200 OK`: 返回 `PaginatedResponse`，`items` 为 `FitnessLogOut` 数组。

---

### 4.3 查询健身统计

```http
GET /api/fitness/stats
```

> **PRD 映射**: F-19（健身频率统计）  
> **前端页面**: 统计分析 (`analytics.html`)  

**认证**: 需要

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `period` | `string` | `"week"` | `week` 或 `month` |

**成功响应** `200 OK`:
```json
{
  "total_sessions": 8,
  "total_minutes": 360,
  "type_distribution": {
    "深蹲": 3,
    "瑜伽": 2,
    "游泳": 2,
    "力量训练": 1
  }
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `total_sessions` | `int` | 该周期内健身总次数 |
| `total_minutes` | `int` | 该周期内累计时长（仅统计填写了时长的记录） |
| `type_distribution` | `dict` | 运动类型分布，key=类型名，value=次数 |

---

### 4.4 查询单条健身记录

```http
GET /api/fitness/{fitness_id}
```

**认证**: 需要  
**响应**: `200` — `FitnessLogOut` / `404` — 不存在

---

### 4.5 编辑健身记录

```http
PATCH /api/fitness/{fitness_id}
```

> **PRD 映射**: F-12（编辑记录）  

**认证**: 需要  
**请求体**: 所有字段可选（同创建 Schema，但 omit_unset）  
**响应**: `200` — 更新后的记录 / `404` — 不存在

---

### 4.6 删除健身记录

```http
DELETE /api/fitness/{fitness_id}
```

> **PRD 映射**: F-12（删除记录）  

**认证**: 需要  
**响应**: `200` — `{"message": "记录已删除"}` / `404` — 不存在

---

## 5. 体重记录 (`/api/weight`)

体重记录模块涵盖 **创建、查询、编辑、删除、统计与趋势**，对应 PRD 功能编号 F-14 至 F-16, F-20, F-21。

**业务规则** (PRD §2.2.3):
- 体重范围: **20 kg ~ 500 kg**
- 支持单位: `kg` 或 `lbs`
- 建议每日仅录入一次，但不做强限制

### 5.1 录入体重记录

```http
POST /api/weight
```

> **PRD 映射**: F-14, F-15  
> **前端页面**: 体重记录 (`weight.html`)  

**认证**: 需要

**请求体** (JSON):
| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `weight_value` | `decimal` | ✓ | 体重数值，20-500 |
| `unit` | `string` | × | 单位: `"kg"` 或 `"lbs"`，默认 `"kg"` |
| `log_date` | `date` | × | 记录日期，默认当天 |
| `notes` | `string` | × | 备注 |

**请求示例**:
```json
{
  "weight_value": 72.5,
  "unit": "kg",
  "log_date": "2026-07-17",
  "notes": "空腹测量"
}
```

**成功响应** `201 Created`:
```json
{
  "weight_id": "f1e2d3c4-...",
  "user_id": "b558d406-...",
  "weight_value": "72.5",
  "unit": "kg",
  "log_date": "2026-07-17",
  "notes": "空腹测量",
  "created_at": "2026-07-17T11:30:00"
}
```

---

### 5.2 查询体重记录列表

```http
GET /api/weight
```

> **PRD 映射**: F-21（历史记录列表）  

**认证**: 需要

**查询参数**: `page`, `page_size`, `start_date`, `end_date`（同跑步记录列表）。

---

### 5.3 查询体重统计

```http
GET /api/weight/stats
```

> **PRD 映射**: F-20（体重变化图信息）  
> **前端页面**: 体重记录 (`weight.html`)、统计分析 (`analytics.html`)  

**认证**: 需要

**成功响应** `200 OK`:
```json
{
  "latest_weight": 71.8,
  "highest_weight": 78.0,
  "lowest_weight": 65.5,
  "latest_unit": "kg",
  "data_points": 42
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `latest_weight` | `float\|null` | 最新体重值 |
| `highest_weight` | `float\|null` | 历史最高值 |
| `lowest_weight` | `float\|null` | 历史最低值 |
| `latest_unit` | `string` | 最新记录的单位 |
| `data_points` | `int` | 累计记录条数 |

---

### 5.4 查询体重变化趋势

```http
GET /api/weight/trend
```

> **PRD 映射**: F-20（折线图数据）  
> **前端页面**: 体重记录 (`weight.html`)、统计分析 (`analytics.html`)  

**认证**: 需要

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `days` | `int` | `90` | 回溯天数，7-365 |

**请求示例**:
```
GET /api/weight/trend?days=30
```

**成功响应** `200 OK`:
```json
[
  {"date": "2026-06-18", "weight": 73.0, "unit": "kg"},
  {"date": "2026-06-20", "weight": 72.5, "unit": "kg"},
  {"date": "2026-06-25", "weight": 72.0, "unit": "kg"},
  {"date": "2026-07-01", "weight": 71.5, "unit": "kg"},
  {"date": "2026-07-17", "weight": 71.8, "unit": "kg"}
]
```

> **说明**: 返回数组按日期升序排列，前端可直接用于 Chart.js / Recharts 折线图。同一天多条记录会全部返回。

---

### 5.5 查询单条 / 编辑 / 删除

```http
GET    /api/weight/{weight_id}    # 查询单条
PATCH  /api/weight/{weight_id}    # 编辑 (F-16)
DELETE /api/weight/{weight_id}    # 删除 (F-16)
```

**认证**: 需要  
**响应**: 同跑步记录对应端点模式。

---

## 6. 运动类型 (`/api/exercise-types`)

> **PRD 映射**: F-09, F-13

### 6.1 获取运动类型列表

```http
GET /api/exercise-types
```

**认证**: 不需要（公开端点）

**查询参数**:
| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `preset_only` | `bool` | `false` | `true` 仅返回预设 15 种；`false` 返回全部 |

**成功响应** `200 OK`:
```json
[
  {"type_id": 1, "type_name": "跑步", "is_preset": true},
  {"type_id": 2, "type_name": "游泳", "is_preset": true},
  {"type_id": 3, "type_name": "骑行", "is_preset": true}
]
```

> **前端用法**: 健身记录页的运动类型下拉框可直接调用此接口获取可选项。

### 6.2 添加自定义运动类型

```http
POST /api/exercise-types
```

> **PRD 映射**: F-13（自定义健身项目）  

**认证**: 需要

**请求体**:
```json
{
  "type_name": "攀岩"
}
```

**成功响应** `201 Created`:
```json
{
  "type_id": 16,
  "type_name": "攀岩",
  "is_preset": false
}
```

**错误**: `409` — `运动类型 '攀岩' 已存在`

---

## 7. 仪表盘 (`/api/dashboard`)

### 7.1 获取仪表盘总览

```http
GET /api/dashboard
```

> **PRD 映射**: F-17（仪表盘总览）  
> **前端页面**: 仪表盘 (`dashboard.html`)  

**认证**: 需要

**请求示例**:
```
GET /api/dashboard
```

**成功响应** `200 OK`:
```json
{
  "today_running_km": 5.2,
  "week_fitness_count": 4,
  "latest_weight": 71.8,
  "latest_weight_unit": "kg"
}
```

**字段说明**:
| 字段 | 类型 | 说明 |
|------|------|------|
| `today_running_km` | `float` | 今日累计跑步距离 |
| `week_fitness_count` | `int` | 本周累计健身次数（周一至今天） |
| `latest_weight` | `float\|null` | 最新体重值，没有记录时为 null |
| `latest_weight_unit` | `string` | 最新体重单位 |

---

## 8. 健康检查 (`/api/health`)

### 8.1 服务健康状态

```http
GET /api/health
```

**认证**: 不需要（公开端点）

**成功响应** `200 OK`:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "ok"
}
```

**数据库异常时**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "error: (2003, \"Can't connect to MySQL server on 'localhost'\")"
}
```

> **运维用途**: 可用于 K8s liveness/readiness probe 或监控报警。

---

## 9. 全局规范

### 9.1 认证方式

所有受保护端点需要在请求头中携带 JWT Token:

```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

- **签发**: 注册或登录成功后返回
- **有效期**: 24 小时（`JWT_EXPIRE_MINUTES=1440`）
- **算法**: HS256
- **载荷**: `{"sub": "<user_id>", "exp": <expire_timestamp>}`

无 Token 或 Token 过期时返回 `403` 或 `401`。

### 9.2 分页规范

所有列表接口统一使用 `PaginatedResponse`:

| 查询参数 | 类型 | 默认值 | 范围 |
|----------|------|--------|------|
| `page` | `int` | 1 | ≥ 1 |
| `page_size` | `int` | 20 | 1–100 |

### 9.3 日期格式

- **请求体**: `"YYYY-MM-DD"` (如 `"2026-07-17"`)
- **查询参数**: 同上
- **响应体**: `"YYYY-MM-DD"` (date 类型)，`"YYYY-MM-DDTHH:MM:SS"` (datetime 类型)

### 9.4 通用校验规则

所有受保护端点的 `log_date` 字段均校验 **不能为未来日期**。违反规则返回 `422`。

### 9.5 CORS

开发阶段允许所有来源 (`allow_origins=["*"]`)。生产环境应修改为前端实际域名。

### 9.6 ID 字段命名

各模块使用独立的 ID 字段名，体现领域语义：

| 模块 | ID 字段 | JSON key |
|------|---------|----------|
| 跑步 | `log_id` | `log_id` |
| 健身 | `fitness_id` | `fitness_id` |
| 体重 | `weight_id` | `weight_id` |
| 用户 | `user_id` | `user_id` |

> **REST 路由**: 全模块统一使用 `{id}` 路径参数，避免前端需要记忆不同参数名。例如 `DELETE /api/running/{log_id}` 路径中参数名为 `log_id`。

### 9.7 错误响应格式

**校验失败 (422)** — Pydantic 自动生成:
```json
{
  "detail": [
    {
      "type": "less_than_equal",
      "loc": ["body", "distance_km"],
      "msg": "Input should be less than or equal to 100",
      "input": 999,
      "ctx": {"le": 100}
    }
  ]
}
```

> `loc` 数组第二个元素指向出错的 JSON 字段名。

**业务错误 (400/401/404/409)**:
```json
{
  "detail": "人类可读的错误描述"
}
```

---

## 10. 前端页面 ↔ API 映射

基于原型文件 (`prototype/Sport-App原型.zip`)，每个 HTML 页面对应的 API 端点如下：

| 原型页面 | 文件 | 需调用的 API |
|----------|------|-------------|
| **落地页** | `landing.html` | 无需 API（纯展示） |
| **注册页** | `register.html` | `POST /api/auth/register` |
| **登录页** | `login.html` | `POST /api/auth/login` |
| **仪表盘** | `dashboard.html` | `GET /api/dashboard`, `GET /api/running/stats?period=week` |
| **跑步记录** | `running.html` | `POST/GET/PATCH/DELETE /api/running` |
| **健身记录** | `fitness.html` | `POST/GET/PATCH/DELETE /api/fitness`, `GET /api/exercise-types` |
| **体重记录** | `weight.html` | `POST/GET/PATCH/DELETE /api/weight`, `GET /api/weight/stats`, `GET /api/weight/trend` |
| **统计分析** | `analytics.html` | `GET /api/running/stats`, `GET /api/fitness/stats`, `GET /api/weight/stats`, `GET /api/weight/trend` |
| **个人中心** | `profile.html` | `GET/PATCH /api/auth/me`, `POST /api/auth/change-password` |

### 10.1 典型前端调用流程

#### 新用户注册流程
```
register.html → POST /api/auth/register → 200 → 获得 token → 跳转 dashboard
```

#### 登录流程
```
login.html → POST /api/auth/login → 200 → 获得 token → 存储 localStorage → 跳转 dashboard
```

#### 仪表盘加载
```
dashboard.html → Promise.all([
  GET /api/dashboard,
  GET /api/running/stats?period=week
]) → 渲染 KPI 卡片
```

#### 跑步记录录入
```
running.html → 用户填表 → POST /api/running → 刷新列表 GET /api/running
```

#### 统计分析页加载
```
analytics.html → Promise.all([
  GET /api/running/stats?period=week,
  GET /api/running/stats?period=month,
  GET /api/fitness/stats?period=week,
  GET /api/weight/stats,
  GET /api/weight/trend?days=90
]) → 渲染各图表
```

---

## 附录 A: API 端点速查表

| 方法 | 端点 | 认证 | 说明 | PRD |
|------|------|------|------|-----|
| `POST` | `/api/auth/register` | — | 用户注册（自动登录） | F-01 |
| `POST` | `/api/auth/login` | — | 用户登录 | F-02 |
| `GET` | `/api/auth/me` | ✓ | 获取个人信息 | F-04 |
| `PATCH` | `/api/auth/me` | ✓ | 更新个人信息 | F-04 |
| `POST` | `/api/auth/change-password` | ✓ | 修改密码 | — |
| `POST` | `/api/running` | ✓ | 录入跑步记录 | F-05,06,07 |
| `GET` | `/api/running` | ✓ | 跑步记录列表 | F-21 |
| `GET` | `/api/running/stats` | ✓ | 跑步周/月统计 | F-18 |
| `GET` | `/api/running/{id}` | ✓ | 单条跑步记录 | — |
| `PATCH` | `/api/running/{id}` | ✓ | 编辑跑步记录 | F-08 |
| `DELETE` | `/api/running/{id}` | ✓ | 删除跑步记录 | F-08 |
| `POST` | `/api/fitness` | ✓ | 录入健身记录 | F-09,10,11 |
| `GET` | `/api/fitness` | ✓ | 健身记录列表 | F-21 |
| `GET` | `/api/fitness/stats` | ✓ | 健身频率统计 | F-19 |
| `GET` | `/api/fitness/{id}` | ✓ | 单条健身记录 | — |
| `PATCH` | `/api/fitness/{id}` | ✓ | 编辑健身记录 | F-12 |
| `DELETE` | `/api/fitness/{id}` | ✓ | 删除健身记录 | F-12 |
| `POST` | `/api/weight` | ✓ | 录入体重记录 | F-14,15 |
| `GET` | `/api/weight` | ✓ | 体重记录列表 | F-21 |
| `GET` | `/api/weight/stats` | ✓ | 体重统计摘要 | F-20 |
| `GET` | `/api/weight/trend` | ✓ | 体重趋势数据 | F-20 |
| `GET` | `/api/weight/{id}` | ✓ | 单条体重记录 | — |
| `PATCH` | `/api/weight/{id}` | ✓ | 编辑体重记录 | F-16 |
| `DELETE` | `/api/weight/{id}` | ✓ | 删除体重记录 | F-16 |
| `GET` | `/api/exercise-types` | — | 运动类型列表 | F-09 |
| `POST` | `/api/exercise-types` | ✓ | 自定义运动类型 | F-13 |
| `GET` | `/api/dashboard` | ✓ | 仪表盘总览 | F-17 |
| `GET` | `/api/health` | — | 健康检查 | — |

> **总计**: 31 个 API 端点，覆盖 19 个 PRD 功能编号。

---

## 附录 B: HTTP 状态码速查

| 码 | 含义 | 本 API 中的场景 |
|----|------|----------------|
| `200` | OK | GET / PATCH / DELETE 成功 |
| `201` | Created | POST 新建资源 |
| `400` | Bad Request | 业务规则冲突 |
| `401` | Unauthorized | Token 无效或密码错误 |
| `403` | Forbidden | 缺少 Authorization 头 |
| `404` | Not Found | 资源不存在 |
| `409` | Conflict | 用户名/邮箱/运动类型重复 |
| `422` | Unprocessable | 请求体格式校验失败 |

---

> **文档结束** — 本文件为 VibeSport v1.0.0 后端 API 的权威参考，应与 [PRD.md](../PRD.md) 及 [database/init.sql](../database/init.sql) 保持一致。
