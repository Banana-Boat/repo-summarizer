package com.summarizer;

import com.alibaba.fastjson.JSON;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.EnumDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.TypeDeclaration;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.summarizer.pojo.JClass;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.List;

public class Main {
  public static void main(String[] args) {
    File file = new File("origin/DayOfWeek.java");
    try {
      CompilationUnit cu = StaticJavaParser.parse(file);
      cu.accept(new VoidVisitorAdapter<Void>() {
        @Override
        public void visit(CompilationUnit cu, Void arg) {
          super.visit(cu, arg);
          // 获取顶层的类 / 接口中的所有方法
          cu.findAll(ClassOrInterfaceDeclaration.class).forEach(coi -> {
            // 拼接实现接口
            StringBuilder implTypes = new StringBuilder();
            coi.getImplementedTypes().forEach(t -> implTypes.append(t).append(", "));
            if (implTypes.length() > 0) implTypes.delete(implTypes.length() - 2, implTypes.length());

            // 拼接继承类
            StringBuilder extendsTypes = new StringBuilder();
            coi.getExtendedTypes().forEach(e -> extendsTypes.append(e).append(", "));
            if (extendsTypes.length() > 0) extendsTypes.delete(extendsTypes.length() - 2, extendsTypes.length());

            String signature = (coi.isInterface() ? "interface " : "class ") + coi.getNameAsString() +
                (extendsTypes.isEmpty() ? "" : " extends " + extendsTypes) +
                (implTypes.isEmpty() ? "" : " implements " + implTypes);


            String jsonString = JSON.toJSONString(new JClass(
                coi.getNameAsString(),
                signature,
                extractMethods(coi),
                cu.getPackageDeclaration().get().getNameAsString(),
                file.getAbsolutePath()
            ));
            System.out.println(jsonString);

          });

          // 获取枚举类中的所有方法
          cu.findAll(EnumDeclaration.class).forEach(e -> {
            // 拼接实现接口
            StringBuilder implTypes = new StringBuilder();
            e.getImplementedTypes().forEach(t -> implTypes.append(t).append(", "));
            if (implTypes.length() > 0) implTypes.delete(implTypes.length() - 2, implTypes.length());

            String signature = "enum " + e.getNameAsString() +
                (implTypes.isEmpty() ? "" : " implements " + implTypes);

            String jsonString = JSON.toJSONString(new JClass(
                e.getNameAsString(),
                signature,
                extractMethods(e),
                cu.getPackageDeclaration().get().getNameAsString(),
                file.getAbsolutePath()
            ));
            System.out.println(jsonString);
          });


        }
      }, null);

    } catch (FileNotFoundException e) {
      e.printStackTrace();
    }


  }

  // 提取class / interface / enum中所有方法
  public static List<String> extractMethods(TypeDeclaration cu) {
    ArrayList<String> methods = new ArrayList<>();

    cu.findAll(MethodDeclaration.class).forEach(md -> {
      // 忽略构造器 / toString / hashCode / equals 方法
      if (md.isConstructorDeclaration() ||
          md.getNameAsString().equals("toString") ||
          md.getNameAsString().equals("hashCode") ||
          md.getNameAsString().equals("equals")) {
        return;
      }

      StringBuilder params = new StringBuilder();
      md.getParameters().forEach(p -> params.append(p.getType()).append(" ").append(p.getName()).append(", "));
      if (params.length() > 0) params.delete(params.length() - 2, params.length());

      String signature = md.getType() + " " + md.getName() + "(" + params + ")";
      String body = md.getBody().get().toString();
      methods.add(signature + body);
    });

    return methods;
  }
}