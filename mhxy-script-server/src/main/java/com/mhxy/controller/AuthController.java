package com.mhxy.controller;

import com.mhxy.dto.ApiResponse;
import com.mhxy.dto.LoginRequest;
import com.mhxy.entity.SysUser;
import lombok.extern.slf4j.Slf4j;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * 认证控制器
 * <p>
 * 当前为开发阶段的占位实现，使用内存数据验证。
 * TODO: 正式上线前需对接数据库 + JWT/Bcrypt
 * </p>
 */
@Slf4j
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    // ===== 开发环境硬编码账号（仅用于开发调试，正式环境必须对接数据库）=====
    private static final String DEV_USERNAME = "admin";
    private static final String DEV_PASSWORD = "admin123";

    /**
     * 登录
     * <p>TODO: 替换为数据库查询 + BCrypt 密码校验 + JWT 令牌签发</p>
     */
    @PostMapping("/login")
    public ApiResponse<Map<String, Object>> login(@RequestBody LoginRequest request) {
        log.info("用户登录: {}", request.getUsername());

        if (DEV_USERNAME.equals(request.getUsername()) && DEV_PASSWORD.equals(request.getPassword())) {
            Map<String, Object> data = new HashMap<>();
            data.put("token", UUID.randomUUID().toString());
            data.put("userId", 1L);
            data.put("username", "admin");
            data.put("balance", 1000000);

            SysUser user = new SysUser();
            user.setId(1L);
            user.setUsername("admin");
            user.setBalance(1000000);
            data.put("userInfo", user);

            return ApiResponse.success("登录成功", data);
        }

        return ApiResponse.fail(401, "用户名或密码错误");
    }

    /**
     * 登出
     * <p>TODO: 实现 Token 失效机制（如 Redis 黑名单）</p>
     */
    @PostMapping("/logout")
    public ApiResponse<Void> logout() {
        log.debug("用户登出");
        return ApiResponse.success("登出成功", null);
    }

    /**
     * 获取当前登录用户信息
     * <p>TODO: 从 Token / SecurityContext 中解析用户身份</p>
     */
    @GetMapping("/userinfo")
    public ApiResponse<SysUser> getUserInfo() {
        SysUser user = new SysUser();
        user.setId(1L);
        user.setUsername("admin");
        user.setPhone("13800138000");
        user.setEmail("admin@mhxy.com");
        user.setBalance(1000000);
        user.setStatus(1);
        return ApiResponse.success(user);
    }

    /**
     * 修改密码
     * <p>TODO: 验证旧密码正确性 + BCrypt 加密新密码 + 写入数据库</p>
     */
    @PutMapping("/password")
    public ApiResponse<Void> updatePassword(@RequestBody Map<String, String> params) {
        String oldPassword = params.get("oldPassword");
        String newPassword = params.get("newPassword");

        if (oldPassword == null || newPassword == null) {
            return ApiResponse.fail("旧密码和新密码不能为空");
        }

        // 安全：绝不将密码明文写入日志
        log.info("用户修改密码（旧密码已脱敏，长度={}；新密码长度={}）",
                oldPassword.length(), newPassword.length());

        // TODO: 实际实现中应验证旧密码并更新数据库
        return ApiResponse.success("密码修改成功", null);
    }
}
