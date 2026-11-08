# VÉRAN

Submission by **Dongyuan Mutu** for the **Applied AI Engineer: Written Challenge**.

This project builds a client advisor tool for VÉRAN, a fictional designer brand. It generates three Chinese WeChat message candidates across six customer communication scenarios.

## Submission

All project submission materials are in the **[submission folder](submission/)**.

| Part | File | Contents |
| --- | --- | --- |
| A | [A_Work_Log.xlsx](submission/A_Work_Log.xlsx) | Work log with eight main steps and screenshot evidence |
| B | [B_Methodology.pdf](submission/B_Methodology.pdf) | Methodology, tool design and evaluation criteria |
| C | [C_Test_Cases.xlsx](submission/C_Test_Cases.xlsx) | 50 test cases, inputs and 150 original messages, all generated with prompt v2.1 |
| D | [D_Evaluation.pdf](submission/D_Evaluation.pdf) | Evaluation results, issue cases, limitations and two supporting screenshots |
| E | [E_Defects_and_Improvements.pdf](submission/E_Defects_and_Improvements.pdf) | Defects and improvements. Actual prompt revisions and manual wording suggestions are labeled separately. |
| Bonus | [Bonus_Tool_Architecture.pdf](submission/Bonus_Tool_Architecture.pdf) | A simple diagram of the tool's input, Python backend, model generation, validation and output |

Download the Excel files to view them. The PDFs can be previewed on GitHub. Report text is in English, and customer messages are in Chinese.

## Repository structure

```text
submission/       Required deliverables A-E
code/             Python tool, web interface, prompts, test data and run records
启动工具.cmd       Local tool launcher for Windows
README.md         Project overview and submission guide
```

## Run the tool

Download and extract the repository, then double-click **启动工具.cmd**. In the browser, choose a scenario, enter the case information and generate three message candidates with a separate advisor note.

Generation requires Python 3.10+, an authenticated Codex CLI and an internet connection. The submission files can be viewed without running the tool.
