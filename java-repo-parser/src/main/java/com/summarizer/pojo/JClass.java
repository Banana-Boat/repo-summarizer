package com.summarizer.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class JClass {
  private String name;
  private String signature;
  private List<JMethod> methods;
  private String path;
}
