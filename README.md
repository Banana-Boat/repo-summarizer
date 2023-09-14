# Repo Summarizer

当程序员首次接触一个复杂软件项目源码时，首先了解源码的目录结构是比较明智的选择。通常项目目录结构的说明会由开发者进行维护，而人工维护会存在费时、更新滞后等问题。**Repo Summarizer** 的初衷即为解决以上问题。

## 实现思路

_待补全..._

## 架构图

```mermaid
flowchart LR
  id_user_repo[/Directory of\nUser Repo/] -->|Load to| id_jrp(Java Repo Parser)

  subgraph Repo-Summarizer
  id_jrp --> Summarizing-Pipeline
  end

  subgraph Summarizing-Pipeline
  id_code1((code)) --> id_llm1(LLM for Code Snippet Sum)
  id_code2((code)) --> id_llm1
  id_code3((code)) --> id_llm1
  id_code4((code)) --> id_llm1
  id_llm1 --> id_code_sum1((code sum))
  id_llm1 --> id_code_sum2((code sum))
  id_llm1 --> id_code_sum3((code sum))
  id_code_sum1 --> id_llm2(LLM for File Sum)
  id_code_sum2 --> id_llm2
  id_code_sum3 --> id_llm2
  id_llm2 --> id_file1((file sum))
  id_llm2 --> id_file2((file sum))
  id_file1 --> id_llm3(LLM for Directory Sum)
  id_file2 --> id_llm3
  id_llm3 --> id_dir((dir sum))
  end

  Summarizing-Pipeline -.Save as.-> id_sum_out[/"Result File\n(*.json)"/]
```

## 运行所需依赖

- [**Java 17+**](https://github.com/o1egl/paseto)（解析 Java 代码所需）
