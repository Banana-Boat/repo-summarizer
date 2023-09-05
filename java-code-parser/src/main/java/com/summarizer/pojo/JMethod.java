package com.summarizer.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class JMethod {
    private String signature;
    private String body;
    private List<JBlock> blocks;
}
