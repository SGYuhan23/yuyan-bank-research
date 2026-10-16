# 当前产业经营研究展示

来源：用户提供的2026-10-16交付包。`dist/` 是唯一 Pages 发布目录；页面、PDF、数据保持交付包研究结论。原项目源码仍在仓库其他目录，不与本版模拟案例混用。

- [交互研究页](https://sgyuhan23.github.io/yuyan-bank-research/)
- [9页研究报告](dist/渝研_产业经营研究报告.pdf)
- [研究正文](研究报告.md)
- [模拟数据及公开来源](dist/data.json)

页面内嵌 data.json 的数据副本，提供预设客户与情景切换。汽车参数确认后显示相应的已计算结果；没有在线模型请求、后台银行接口或真实交易。报告相对路径适配 GitHub Pages 子路径；`#fuling`、`#supplier`、`#evidence` 可直接刷新。

## 验证与复算

Python 仅需标准库；Node 22+、pnpm 11.25.0。先从仓库根目录运行发布快照校验，再执行以下命令：

```sh
cd research-showcase
python -m unittest test_model -v
pnpm install --frozen-lockfile
pnpm test
pnpm run test:deploy
python verify_delivery.py
```

`test_model.py` 会调用 model.py 重建数据；`verify_delivery.py` 核对原交付物哈希、页面内嵌数据与 data.json，防止部署页面与复算产物脱节。报告与页面的交付物未修改，模型输出也未重新设定。

`python model.py` 可单独复算；`python build_page.py` 从 page.html、data.json 和现有 PDF 重建页面。PDF 如需重建，按原交付说明安装 ReportLab 并提供合法授权的 Noto Sans SC 字体；本次发布保留交付 PDF，不重新排版报告。

原始交付说明及 qa 文件保留其当时验证状态；本次另行完成真实浏览器桌面/手机验收。部署通过仓库现有 Pages workflow，原应用继续测试和构建，但不进入新版发布目录。
