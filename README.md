# 树莓派 4.2 寸墨水屏智能看板 (Pi-Mate)

## 1. 项目概述
本项目利用树莓派驱动 4.2 寸电子墨水屏（E-Ink），打造了一个低功耗、高颜值的桌面智能信息看板。
系统基于 Python 开发，实现了时钟分钟级刷新、名言警句定时轮换，并深度优化了墨水屏的中文排版与字体渲染效果。

### ✨ 核心特性
* **精准排版**：采用上中下三段式经典布局，通过 `textbbox` 像素级测量实现时间与日期的绝对居中，以及名言出处的严格右对齐。
* **平滑字体渲染（反锯齿二值化）**：突破原生 1-bit 黑白画布的锯齿限制，采用 256 级灰度（L 模式）绘制矢量文字，辅以自定义阈值卡点二值化，实现媲美印刷级的清秀字体。
* **智能缓存引擎**：读写分离逻辑。屏幕时钟每分钟走字，但网络 API 请求严格控制在每 10 分钟一次，通过本地 JSON 缓存状态，既保证了时效性又避免了 API 封禁。
* **超长文本自适应**：拉取一言（Hitokoto）接口时，自动进行像素级换行测算，若名言超过允许行数则自动舍弃并无缝重试，确保版面不崩塌。

---

## 2. 硬件清单与接线指南

* **主控**：树莓派 4B (系统：Ubuntu 24.04 Server)
* **显示设备**：WEIFENG 4.2 寸电子墨水屏 (SPI 通信)

**GPIO 物理接线表（BCM 编码对应）：**

| 驱动板引脚 | 线序颜色 | 树莓派物理引脚 (Pin #) | 树莓派功能名 (BCM) |
| :--- | :--- | :--- | :--- |
| **GND** | 蓝色 | 6 / 9 / 14 | Ground |
| **3.3V** | 绿色 | 1 | 3.3V Power |
| **SCL** | 黄色 | 23 | SPI0_SCLK |
| **SDI** | 橙色 | 19 | SPI0_MOSI |
| **RES** | 红色 | 11 | GPIO 17 |
| **D/C** | 棕色 | 22 | GPIO 25 |
| **CS** | 灰色 | 24 | SPI0_CE0 |
| **BUSY** | 白色 | 18 | GPIO 24 |

---

## 3. 环境准备与依赖安装

**1. 开启 SPI 硬件接口**
在 `/boot/firmware/config.txt` 中添加 `dtparam=spi=on` 并重启。

**2. 安装系统级依赖库**
```bash
sudo apt update
sudo apt install -y python3-pip python3-pil python3-numpy python3-spidev python3-rpi.gpio python3-gpiozero fonts-wqy-microhei
```

**3. 安装 Python 第三方库**
```bash
sudo pip3 install requests sxtwl --break-system-packages
```

---

## 4. 自动化部署

为实现时钟跳字，将主脚本挂载为每分钟执行的后台系统任务：

1. 编辑定时任务：`sudo crontab -e`
2. 在文件末尾添加规则：
   ```bash
   * * * * * /usr/bin/python3 /home/wf/papperscreen/smart_screen.py >> /home/wf/papperscreen/log.txt 2>&1
   ```
