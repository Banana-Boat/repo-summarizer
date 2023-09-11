package com.summarizer.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;
@Data
@AllArgsConstructor
public class JRepo {
    private JPackage mainPackage;
    private Integer nodeCount;
}
