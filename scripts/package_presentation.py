"""Collect interview materials and a self-contained local runtime in one folder."""
import json
from pathlib import Path
import shutil

from veran_advisor.prompt_loader import PROMPT_VERSION, ROOT


def copy_tree(source, target):
    for source_file in source.rglob("*"):
        if not source_file.is_file() or "__pycache__" in source_file.parts or source_file.suffix in {".pyc", ".pyo"}:
            continue
        destination = target / source_file.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, destination)


def main():
    folder = ROOT / "presentation"
    folder.mkdir(exist_ok=True)
    (folder / ".gitignore").write_text("runtime/.local/\n__pycache__/\n*.py[cod]\n*.log\n", encoding="utf-8")
    runtime = folder / "runtime"
    for name in ("veran_advisor", "config", "prompts"):
        copy_tree(ROOT / name, runtime / name)
    copy_tree(ROOT / "reports", folder / "report")
    copy_tree(ROOT / "docs", folder / "materials")
    copy_tree(ROOT / "evidence", folder / "evidence")
    example_dir = runtime / "data/examples"
    example_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(ROOT / "data/examples/case_001.json", example_dir / "case_001.json")
    (folder / "使用说明.txt").write_text("""VÉRAN 面试展示包

1. 双击「开始这里.html」，查看展示导航。
2. 双击「启动现场演示.vbs」。浏览器会打开 http://127.0.0.1:8765/。
3. 在页面选择六种场景之一，填写面试官给的新案例。
4. 点击「生成三条候选话术」。结果来自本次实际模型调用。
5. 可以复制话术，或点击「保存本次输入与结果」下载记录。
6. 演示结束，点击页面右上角「关闭演示」。

如果双击后没有打开页面：
- 先尝试在浏览器打开 http://127.0.0.1:8765/。
- 仍打不开时，双击「备用启动.cmd」查看启动信息。

环境：本机需要 Python 3.10+、已登录的 Codex CLI，以及可用网络。
本文件夹包含运行代码，但不包含 Python、模型或登录凭据。
报告及 50 个案例可以离线打开，现场生成新案例需要网络和本机登录。
所有案例均为虚构资料。生成结果需要顾问审核，不会自动发送。

展示内容：
- report/report.html：完整项目报告，含工作日志、方法、50 例结果、评估和缺陷。
- report/cases.json：50 例输入及 150 条模型原始输出。
- report/evaluation.json：简单评估结果。
- materials/：品牌设定、工作日志、评估方法。
- runtime/prompts/：六场景提示词；runtime/veran_advisor/ 中保留实际生成逻辑。
- evidence/：可移植的原始请求、输出和版本记录。

现场生成记录保存在 runtime/.local/ 下，不属于原来的 50 例测试集。
提交材料中的早期聊天截图、生成/评估截图和报告视觉检查仍待补齐。
""", encoding="utf-8-sig")
    launcher = '''Option Explicit
Dim shell, fso, folder, runtime, pythonw, result
Set shell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")
folder = fso.GetParentFolderName(WScript.ScriptFullName)
runtime = fso.BuildPath(folder, "runtime")
shell.CurrentDirectory = runtime
pythonw = shell.ExpandEnvironmentStrings("%USERPROFILE%") & "\\miniconda3\\pythonw.exe"
If Not fso.FileExists(pythonw) Then pythonw = "pythonw.exe"
On Error Resume Next
result = shell.Run(Chr(34) & pythonw & Chr(34) & " -m veran_advisor.demo", 0, False)
If Err.Number <> 0 Then
  MsgBox "Unable to start. Please use the .cmd launcher or check Python installation.", 48, "VERAN"
End If
'''
    (folder / "启动现场演示.vbs").write_bytes(launcher.replace("\n", "\r\n").encode("ascii"))
    fallback = '''@echo off
chcp 65001 >nul
cd /d "%~dp0runtime"
if exist "%USERPROFILE%\\miniconda3\\python.exe" (
  "%USERPROFILE%\\miniconda3\\python.exe" -m veran_advisor.demo
) else (
  python -m veran_advisor.demo
)
if errorlevel 1 pause
'''
    (folder / "备用启动.cmd").write_bytes(fallback.replace("\n", "\r\n").encode("ascii"))
    index = '''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VÉRAN · 面试展示包</title><style>body{font:17px/1.8 system-ui,'Microsoft YaHei',sans-serif;margin:0;background:#f3f4ee;color:#1d2520}main{max-width:920px;margin:50px auto;padding:0 24px}.brand{font-size:38px;letter-spacing:6px}h1{font-size:28px;margin:10px 0}p{color:#59635b}.cards{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin:26px 0}.card{background:#fff;border:1px solid #d5dcd1;padding:22px}a{color:#253b2a;text-underline-offset:5px}.live{background:#d6ebaa;padding:24px}.small{font-size:14px}h2{font-size:20px;margin:0 0 8px}@media(max-width:620px){.cards{grid-template-columns:1fr}}</style><main><div class="brand">VÉRAN</div><h1>面试展示包</h1><p>六种客户沟通场景 · 50 个案例 · 150 条实际生成话术</p><div class="live"><h2>现场验证新案例</h2><div>请在本文件夹中双击 <b>启动现场演示.vbs</b>。</div><div>浏览器打开后，选择场景、填写新案例，再点击生成。</div><p class="small">需要本机 Python、已登录的 Codex 和可用网络。双击无响应时可使用「备用启动.cmd」。</p></div><div class="cards"><div class="card"><h2>完整项目报告</h2><a href="report/report.html">打开报告</a><p class="small">工作日志、方法、案例、评估、缺陷和架构。</p></div><div class="card"><h2>50 个案例与输出</h2><a href="report/report.html#cases">查看全部案例</a><p class="small">50 组输入及对应的三条模型原始话术。</p></div><div class="card"><h2>评估结果</h2><a href="report/report.html#evaluation">查看评估</a><p class="small">40 例通过，10 例需修改。评估由 Codex 辅助完成。</p></div><div class="card"><h2>缺陷与修改</h2><a href="report/report.html#defects">查看修改前后对比</a><p class="small">保留真实问题和版本，不把人工改写冒充模型输出。</p></div></div><p class="small">报告与案例可离线查看。现场新案例使用实际模型调用。完整操作说明见「使用说明.txt」。截图和报告视觉检查仍待补齐。</p></main></html>'''
    (folder / "开始这里.html").write_text(index, encoding="utf-8")
    (folder / "package_info.json").write_text(json.dumps({"prompt_version": PROMPT_VERSION, "entry": "开始这里.html", "launcher": "启动现场演示.vbs", "live_url": "http://127.0.0.1:8765/", "report": "report/report.html", "cases": 50, "messages": 150, "requires": ["Python 3.10+", "authenticated local Codex CLI", "network for new generation"]}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(folder))


if __name__ == "__main__":
    main()
