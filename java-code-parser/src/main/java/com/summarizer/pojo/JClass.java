package com.summarizer.pojo;

import java.util.List;

public class JClass {
  private String name;
  private String signature;
  private List<String> methods;
  private String packageName;
  private String filePath;

  public JClass(String name, String signature, List<String> methods, String packageName, String filePath) {
    this.name = name;
    this.signature = signature;
    this.methods = methods;
    this.packageName = packageName;
    this.filePath = filePath;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getSignature() {
    return signature;
  }

  public void setSignature(String signature) {
    this.signature = signature;
  }

  public List<String> getMethods() {
    return methods;
  }

  public void setMethods(List<String> methods) {
    this.methods = methods;
  }

  public String getPackageName() {
    return packageName;
  }

  public void setPackageName(String packageName) {
    this.packageName = packageName;
  }

  public String getFilePath() {
    return filePath;
  }

  public void setFilePath(String filePath) {
    this.filePath = filePath;
  }

  @Override
  public String toString() {
    return "JClass{" +
        "name='" + name + '\'' +
        ", signature='" + signature + '\'' +
        ", methods=" + methods +
        ", packageName='" + packageName + '\'' +
        ", filePath='" + filePath + '\'' +
        '}';
  }
}
