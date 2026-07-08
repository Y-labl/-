package com.mhxy;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * 梦幻西游自动化图色脚本 - 启动类
 */
@SpringBootApplication
public class MhxyApplication {

    public static void main(String[] args) {
        // 关闭 headless 模式（需要使用 Robot 截图，必须连接桌面）
        System.setProperty("java.awt.headless", "false");

        SpringApplication.run(MhxyApplication.class, args);
        System.out.println("╔═══════════════════════════════════════════╗");
        System.out.println("║     梦幻西游自动化图色脚本 已启动!         ║");
        System.out.println("║     访问 http://localhost:8888       ║");
        System.out.println("╚═══════════════════════════════════════════╝");
    }
}
