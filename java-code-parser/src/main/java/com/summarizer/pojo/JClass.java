package com.summarizer.pojo;

import java.util.List;

public class JClass {
  private String name;
  private String signature;
  private List<String> methods;
  private String path;

  public JClass(String name, String signature, List<String> methods, String path) {
    this.name = name;
    this.signature = signature;
    this.methods = methods;
    this.path = path;
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

  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  @Override
  public String toString() {
    return "JClass{" +
        "name='" + name + '\'' +
        ", signature='" + signature + '\'' +
        ", methods=" + methods +
        ", path='" + path + '\'' +
        '}';
  }
}
