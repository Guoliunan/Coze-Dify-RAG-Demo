# Coze + Dify RAG Demo

服装品牌智能客服 Agent 搭建与 RAG 参数调优实验项目。

## 项目概述

本项目包含两个子项目：

1. **Coze 智能客服 Agent**：在 Coze 低代码平台上搭建端到端智能客服系统 [https://www.coze.cn/work_flow?space_id=7539860429355991082&workflow_id=7633648789806661682&force_stay=1]
2. **Dify RAG 参数调优**：在 Dify 平台上设计对比实验，量化分析不同配置对 RAG 检索效果的影响 [https://cloud.dify.ai/apps]

## 目录结构

```
coze-dify-rag-demo/
├── README.md                          # 项目总览
├── coze-agent/                        # Coze Agent 相关
│   ├── 意图识别Prompt.md
│   └── Coze客服Agent面试准备.md
├── dify-rag/                          # Dify RAG 相关
│   ├── 搭建与调优指南.md
│   ├── 实验总结报告.md
│   └── 自动化测试脚本.py
├── knowledge-base/                    # 知识库文档
│   ├── 产品FAQ.md
│   ├── 退换货政策.md
│   └── 产品帮助中心.md
└── test-results/                      # 测试结果（示例）
    └── *.md/*.csv
```

## 核心成果

### Coze 智能客服 Agent

- **意图识别准确率**：90%+
- **知识库问题回答准确率**：85%+
- **核心能力**：
  - 4 分类意图识别（商品咨询/退换货/物流/其他）
  - 双知识库架构（产品 FAQ + 退换货政策）
  - Few-shot + JSON 输出格式
  - 知识约束 Prompt 减少幻觉

### Dify RAG 参数调优

- **通过率提升**：55% → 70%（+15%）
- **幻觉控制**：20/20 知识库外问题正确拒答
- **实验设计**：4 轮对比实验
- **核心发现**：
  1. 知识库文档覆盖率是决定性因素
  2. 切片策略影响 > 检索参数影响
  3. 按标题切片优于固定长度切片
  4. 相似度阈值是控制幻觉的关键

## 快速开始

### Coze Agent

详见[https://www.coze.cn/work_flow?space_id=7539860429355991082&workflow_id=7633648789806661682&force_stay=1]

### Dify RAG 测试

1. 在 Dify 应用页面获取 API Key
2. 修改 `dify-rag/自动化测试脚本.py` 中的 API_KEY 和 BASE_URL
3. 运行测试：
   ```bash
   python dify-rag/自动化测试脚本.py

   ```

## 许可证

MIT License