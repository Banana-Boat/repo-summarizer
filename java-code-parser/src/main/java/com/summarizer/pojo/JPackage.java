package com.summarizer.pojo;

import java.util.List;

public class JPackage {
  private String name;
  private String path;
  private List<JClass> classes;
  private List<JPackage> subPackages;

  public JPackage(String name, String path, List<JClass> classes, List<JPackage> subPackages) {
    this.name = name;
    this.path = path;
    this.classes = classes;
    this.subPackages = subPackages;
  }

  public String getName() {
    return name;
  }

  public void setName(String name) {
    this.name = name;
  }

  public String getPath() {
    return path;
  }

  public void setPath(String path) {
    this.path = path;
  }

  public List<JClass> getClasses() {
    return classes;
  }

  public void setClasses(List<JClass> classes) {
    this.classes = classes;
  }

  public List<JPackage> getSubPackages() {
    return subPackages;
  }

  public void setSubPackages(List<JPackage> subPackages) {
    this.subPackages = subPackages;
  }


  @Override
  public String toString() {
    return "JPackage{" +
        "name='" + name + '\'' +
        ", path='" + path + '\'' +
        ", classes=" + classes +
        ", subPackages=" + subPackages +
        '}';
  }
}
