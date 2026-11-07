# Artefact — VÉRAN

中文微信话术生成工具，覆盖六种客户沟通场景。

## 怎么打开

1. **查看提交报告：双击最外层的 `打开报告.html`。** 报告和测试结果可以离线查看。
2. **输入新案例：双击最外层的 `启动工具.cmd`。** 浏览器会自动打开，选择场景、填写信息，再点击生成。

如果你现在看的是 GitHub 网页，先点击 **Code → Download ZIP**，下载后**解压**，再双击上述文件。GitHub 的文件预览不能直接运行这个工具。

生成新话术需要本机安装 Python 3.10+、Codex CLI，并已登录且网络可用。默认地址为 `http://127.0.0.1:8765/`；使用结束后点击页面右上角“关闭工具”。

## 文件结构

```text
打开报告.html       查看报告的入口
启动工具.cmd        运行话术生成工具
submission/         提交材料：报告、50 例结果、评估、方法、工作日志与提示词
code/               工具代码、测试和维护脚本
```

主要结果：**50 个虚构案例、150 条模型实际生成的话术**。Codex 辅助评估结果为 40 例通过、10 例需修改。当前提示词版本为 `veran_scenarios_v2.1`。截图和报告视觉检查仍待补齐。

## 代码运行与维护

以下命令都在 `code` 文件夹中执行：

```powershell
python -m veran_advisor.demo
python -m unittest discover -s tests -v
python -m scripts.build_report
```

`scripts.build_report` 使用已有证据重建报告，不调用模型。批量重新生成请使用 `python -m scripts.batch_generate`；新结果需要重新评估。原始运行记录和题目 PDF 只保留在本机隐藏目录 `.local/`，已从 Git 排除。
