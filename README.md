# Andy's FIRE Tracker

QQQM / VOO 纳指动态定投 Dashboard，基于纳斯达克100 TTM PE 策略。

## 本地运行

```bash
pip install -r requirements.txt
streamlit run app.py
```

## 部署到 Streamlit Community Cloud（免费）

1. 将整个项目 push 到 GitHub 仓库（public 或 private 均可）
2. 访问 https://share.streamlit.io，用 GitHub 账号登录
3. 点击 **New app**，选择仓库、分支、主文件 `app.py`
4. 点击 **Deploy**，几分钟后获得公开链接（格式：`https://xxx.streamlit.app`）
5. 之后每次 push 到 GitHub，Streamlit Cloud 自动重新部署

## 数据更新

- 每次打开页面自动从 Yahoo Finance 拉取最新数据
- 价格缓存 5 分钟，ticker.info 缓存 10 分钟
- 无需额外定时任务

## 定投记录持久化

Streamlit Cloud 文件系统是临时的，记录通过 **导出 CSV → 本地保存 → 下次导入** 方式持久化。

## 文件结构

```
qqqm_dashboard/
├── app.py                  # 主应用（全部逻辑）
├── requirements.txt        # 依赖
├── README.md
└── .streamlit/
    └── config.toml         # 深色主题配置
```
