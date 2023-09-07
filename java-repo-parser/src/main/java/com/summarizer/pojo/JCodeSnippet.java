package com.summarizer.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class JCodeSnippet {
    private String content;
    private List<JCodeSnippet> codeSnippets;
}
