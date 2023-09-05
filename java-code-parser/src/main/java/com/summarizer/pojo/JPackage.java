package com.summarizer.pojo;

import lombok.AllArgsConstructor;
import lombok.Data;

import java.util.List;

@Data
@AllArgsConstructor
public class JPackage {
  private String name;
  private String path;
  private List<JClass> classes;
  private List<JPackage> subPackages;
}
