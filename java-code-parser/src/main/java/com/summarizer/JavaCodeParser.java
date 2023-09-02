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
import com.summarizer.pojo.JPackage;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(name = "JavaCodeParser", mixinStandardHelpOptions = true, version = "JavaCodeParser 1.0")
public class JavaCodeParser implements Runnable {

  @Option(names={"-r", "--repo-dir"}, description = "Path to the directory of repository", required = true)
  private String repoDirPath;

  @Option(names={"-o", "--output"}, description = "Path to the output file")
  private String outputDirPath = "./output.json";

  public static void main(String[] args) {
    int exitCode = new CommandLine(new JavaCodeParser()).execute(args);
    System.exit(exitCode);
  }

  @Override
  public void run() {
    File dir = new File(repoDirPath);
    if (!dir.isDirectory()) return;

    String json = JSON.toJSONString(extractPackage(dir));
    try (FileWriter fw = new FileWriter(outputDirPath)) {
      fw.write(json);
    } catch (Exception e) {
      e.printStackTrace();
    }

    System.out.println("Done!");
  }

  /**
   * 提取一个目录中的所有子包 / 类 / 接口 / 枚举
   */
  public static JPackage extractPackage(File dir) {
    if (!dir.isDirectory()) return null;

    ArrayList<JPackage> subPackages = new ArrayList<>();
    ArrayList<JClass> classes = new ArrayList<>();

    for (File file : dir.listFiles()) {
      if(file.isDirectory()) {
        subPackages.add(extractPackage(file));
      } else {
        if(file.getName().endsWith(".java")) {
          classes.addAll(extractClasses(file));
        }
      }
    }

    return new JPackage(
        dir.getName(),
        dir.getPath(),
        classes,
        subPackages
    );
  }

  /**
   * 提取一个文件中的所有类 / 接口 / 枚举
   */
  public static List<JClass> extractClasses(File file) {
    ArrayList<JClass> classes = new ArrayList<>();

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


            // 拼接签名
            String signature = (coi.isAbstract() ? "abstract " : "") +
                (coi.isInterface() ? "interface " : "class ") + coi.getNameAsString() +
                (extendsTypes.isEmpty() ? "" : " extends " + extendsTypes) +
                (implTypes.isEmpty() ? "" : " implements " + implTypes);

            classes.add(new JClass(
                coi.getNameAsString(),
                signature,
                extractMethods(coi),
                file.getPath()
            ));
          });

          // 获取枚举类中的所有方法
          cu.findAll(EnumDeclaration.class).forEach(e -> {
            // 拼接实现接口
            StringBuilder implTypes = new StringBuilder();
            e.getImplementedTypes().forEach(t -> implTypes.append(t).append(", "));
            if (implTypes.length() > 0) implTypes.delete(implTypes.length() - 2, implTypes.length());

            // 拼接签名
            String signature = "enum " + e.getNameAsString() +
                (implTypes.isEmpty() ? "" : " implements " + implTypes);

            classes.add(new JClass(
                e.getNameAsString(),
                signature,
                extractMethods(e),
                file.getPath()
            ));
          });
        }
      }, null);

    } catch (FileNotFoundException e) {
      e.printStackTrace();
    }

    return classes;
  }

  /**
   * 提取一个类 / 接口 / 枚举中的所有方法
   */
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
      // 忽略空方法
      if (md.getBody().isEmpty()) return;

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