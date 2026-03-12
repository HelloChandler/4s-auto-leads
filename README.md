# 4S店汽车销售线索自动获取系统

## 项目简介
自动监控抖音、快手、小红书等平台的汽车相关评论，识别潜在购车用户，通过AI评分后自动触达，帮助4S店高效获取销售线索。

## 功能特性
- ✅ 多平台实时监控（抖音/快手/小红书）
- ✅ AI智能识别购车意向用户
- ✅ 自动评分分级，优先处理高意向客户
- ✅ 自动去重，避免重复触达
- ✅ 多渠道自动触达（私信/电话）
- ✅ 完整的线索管理和数据统计

## 技术栈
- Python 3.10+
- Playwright（浏览器自动化）
- SQLite（数据存储）
- YAML（配置管理）
- OpenClaw（任务调度、消息触达）

## 部署指南
### Windows
1. 双击运行 `install.bat` 安装依赖
2. 复制 `.env.example` 为 `.env` 并配置相关密钥
3. 修改 `config/settings.yaml` 中的平台账号和配置
4. 双击 `scripts/start.bat` 启动系统

### Linux/Mac
1. 运行 `chmod +x install.sh && ./install.sh`
2. 复制 `.env.example` 为 `.env` 并配置相关密钥
3. 修改 `config/settings.yaml` 中的平台账号和配置
4. 运行 `./scripts/start.sh` 启动系统

## 使用说明
1. 配置平台账号：在 `config/settings.yaml` 中填写各平台的登录信息
2. 配置监控视频：添加需要监控的视频链接到对应平台的任务配置
3. 配置评分规则：根据业务需求调整用户评分权重
4. 配置触达模板：设置私信和电话的话术模板
5. 启动系统后会自动监控评论并处理线索

## 目录结构
```
4s-auto-leads/
├── README.md          # 项目说明文档
├── requirements.txt   # Python依赖包
├── .env               # 环境变量（敏感信息）
├── config/            # 配置文件目录
├── tasks/             # OpenClaw任务定义
├── src/               # 源代码目录
├── data/              # 数据存储目录
├── scripts/           # 启动停止脚本
└── install.sh         # 一键安装脚本
```

## 注意事项
- 请勿泄露 `.env` 和 `config/` 目录下的敏感信息
- 建议使用住宅代理池避免平台账号被封
- 定期备份 `data/leads.db` 数据库文件
- 遵守各平台的使用条款，合理使用本系统