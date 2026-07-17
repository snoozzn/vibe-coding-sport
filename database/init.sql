-- ============================================================
-- VibeSport 数据库初始化脚本
-- 数据库名称: account
-- MySQL 8.0+ (端口 3306)
-- 基于 PRD v1.0.0 第 5 节数据模型
-- 创建日期: 2026-07-17
-- ============================================================

-- 确保客户端与服务端字符集一致
SET NAMES utf8mb4;

-- -----------------------------------------------------------
-- 0. 建库
-- -----------------------------------------------------------
CREATE DATABASE IF NOT EXISTS `account`
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE `account`;

-- -----------------------------------------------------------
-- 1. 用户表 (User)
-- 对应 PRD §5.1
-- 附加字段:
--   login_attempts  - 登录失败计数 (F-01: ≥5次锁定)
--   locked_until    - 账号锁定截止时间 (F-01: 锁定15分钟)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `users` (
    `user_id`          CHAR(36)         NOT NULL                    COMMENT '用户唯一标识 (UUID v4)',
    `username`         VARCHAR(20)      NOT NULL                    COMMENT '用户名, 2-20字符',
    `email`            VARCHAR(255)     NOT NULL                    COMMENT '邮箱地址',
    `password_hash`    VARCHAR(255)     NOT NULL                    COMMENT '密码哈希 (bcrypt/argon2)',
    `avatar_url`       VARCHAR(500)     DEFAULT NULL                COMMENT '头像链接',
    `target_weight_kg` DECIMAL(5,1)     DEFAULT NULL                COMMENT '目标体重 (kg)',
    `login_attempts`   TINYINT UNSIGNED NOT NULL DEFAULT 0          COMMENT '连续登录失败次数',
    `locked_until`     DATETIME         DEFAULT NULL                COMMENT '账号锁定截止时间',
    `created_at`       DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    `updated_at`       DATETIME         NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',

    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_username` (`username`),
    UNIQUE KEY `uk_email`    (`email`),

    -- 用户名: 2-20 字符, 支持中英文/数字/下划线 (MySQL 8.0 CHECK)
    CONSTRAINT `chk_username` CHECK (
        CHAR_LENGTH(`username`) BETWEEN 2 AND 20
    ),

    -- 邮箱基本格式校验
    CONSTRAINT `chk_email` CHECK (
        CHAR_LENGTH(`email`) >= 6 AND `email` LIKE '%_@__%.__%'
    ),

    -- 目标体重: 20 ~ 500 kg
    CONSTRAINT `chk_target_weight` CHECK (
        `target_weight_kg` IS NULL OR (`target_weight_kg` >= 20 AND `target_weight_kg` <= 500)
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';


-- -----------------------------------------------------------
-- 2. 跑步记录表 (RunningLog)
-- 对应 PRD §5.2
-- 业务规则: distance_km ∈ [0.1, 100], log_date ≤ 当天
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `running_logs` (
    `log_id`      CHAR(36)     NOT NULL                COMMENT '记录唯一标识 (UUID v4)',
    `user_id`     CHAR(36)     NOT NULL                COMMENT '所属用户 UUID',
    `distance_km` DECIMAL(5,1) NOT NULL                COMMENT '跑步距离 (公里)',
    `log_date`    DATE         NOT NULL                COMMENT '运动日期',
    `notes`       TEXT         DEFAULT NULL            COMMENT '备注 (感受/天气/路线)',
    `created_at`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (`log_id`),

    -- 复合索引: 按用户+日期查询是最频繁的查询模式
    KEY `idx_running_user_date` (`user_id`, `log_date`),
    KEY `idx_running_date`      (`log_date`),

    CONSTRAINT `fk_running_user` FOREIGN KEY (`user_id`)
        REFERENCES `users`(`user_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- 单次跑步距离: 0.1 ~ 100 km
    CONSTRAINT `chk_distance` CHECK (`distance_km` > 0 AND `distance_km` <= 100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='跑步记录表';


-- -----------------------------------------------------------
-- 3. 健身记录表 (FitnessLog)
-- 对应 PRD §5.3
-- 业务规则: duration_minutes ∈ [1, 480], 预设15种运动类型
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `fitness_logs` (
    `fitness_id`       CHAR(36)     NOT NULL                COMMENT '记录唯一标识 (UUID v4)',
    `user_id`          CHAR(36)     NOT NULL                COMMENT '所属用户 UUID',
    `exercise_type`    VARCHAR(100) NOT NULL                COMMENT '运动类型',
    `duration_minutes` INT          DEFAULT NULL            COMMENT '训练时长 (分钟)',
    `reps_sets`        VARCHAR(50)  DEFAULT NULL            COMMENT '组数×次数, 如 4×12',
    `log_date`         DATE         NOT NULL                COMMENT '运动日期',
    `notes`            TEXT         DEFAULT NULL            COMMENT '备注',
    `created_at`       DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (`fitness_id`),

    KEY `idx_fitness_user_date` (`user_id`, `log_date`),
    KEY `idx_fitness_type`      (`exercise_type`),
    KEY `idx_fitness_date`      (`log_date`),

    CONSTRAINT `fk_fitness_user` FOREIGN KEY (`user_id`)
        REFERENCES `users`(`user_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- 时长: 1 ~ 480 分钟
    CONSTRAINT `chk_duration` CHECK (
        `duration_minutes` IS NULL OR (`duration_minutes` >= 1 AND `duration_minutes` <= 480)
    ),

    -- duration_minutes 和 reps_sets 至少填一个
    CONSTRAINT `chk_fitness_entry` CHECK (
        `duration_minutes` IS NOT NULL OR `reps_sets` IS NOT NULL
    )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='健身记录表';


-- -----------------------------------------------------------
-- 4. 体重记录表 (WeightLog)
-- 对应 PRD §5.4
-- 业务规则: weight_value ∈ [20, 500], unit ∈ ('kg', 'lbs')
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `weight_logs` (
    `weight_id`     CHAR(36)     NOT NULL                COMMENT '记录唯一标识 (UUID v4)',
    `user_id`       CHAR(36)     NOT NULL                COMMENT '所属用户 UUID',
    `weight_value`  DECIMAL(5,1) NOT NULL                COMMENT '体重数值',
    `unit`          VARCHAR(3)   NOT NULL DEFAULT 'kg'   COMMENT '单位: kg / lbs',
    `log_date`      DATE         NOT NULL                COMMENT '记录日期',
    `notes`         TEXT         DEFAULT NULL            COMMENT '备注',
    `created_at`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (`weight_id`),

    KEY `idx_weight_user_date` (`user_id`, `log_date`),
    KEY `idx_weight_date`      (`log_date`),

    CONSTRAINT `fk_weight_user` FOREIGN KEY (`user_id`)
        REFERENCES `users`(`user_id`)
        ON DELETE CASCADE
        ON UPDATE CASCADE,

    -- 体重: 20 ~ 500
    CONSTRAINT `chk_weight` CHECK (`weight_value` >= 20 AND `weight_value` <= 500),

    -- 单位约束
    CONSTRAINT `chk_unit` CHECK (`unit` IN ('kg', 'lbs'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='体重记录表';


-- -----------------------------------------------------------
-- 5. 运动类型预设表
-- 对应 PRD §2.2.2 中预设的 15 种健身类型
-- 用户也可通过 F-13 添加自定义类型 (is_preset = FALSE)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS `exercise_types` (
    `type_id`    INT AUTO_INCREMENT                   COMMENT '类型 ID',
    `type_name`  VARCHAR(100) NOT NULL                COMMENT '运动类型名称',
    `is_preset`  BOOLEAN      NOT NULL DEFAULT TRUE   COMMENT '是否为系统预设',
    `created_at` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',

    PRIMARY KEY (`type_id`),
    UNIQUE KEY `uk_type_name` (`type_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='运动类型预设表';

-- 插入预设运动类型 (PRD §2.2.2)
INSERT INTO `exercise_types` (`type_name`, `is_preset`) VALUES
    ('跑步',     TRUE),
    ('游泳',     TRUE),
    ('骑行',     TRUE),
    ('瑜伽',     TRUE),
    ('力量训练', TRUE),
    ('俯卧撑',   TRUE),
    ('深蹲',     TRUE),
    ('引体向上', TRUE),
    ('跳绳',     TRUE),
    ('普拉提',   TRUE),
    ('拳击',     TRUE),
    ('篮球',     TRUE),
    ('足球',     TRUE),
    ('羽毛球',   TRUE),
    ('乒乓球',   TRUE);


-- ============================================================
-- 验证: 查看所有已创建的表
-- ============================================================
SELECT TABLE_NAME, TABLE_COMMENT, TABLE_ROWS
FROM information_schema.TABLES
WHERE TABLE_SCHEMA = 'account'
ORDER BY TABLE_NAME;
