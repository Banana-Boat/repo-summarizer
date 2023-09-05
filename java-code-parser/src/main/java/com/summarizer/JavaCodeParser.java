package com.summarizer;

import com.alibaba.fastjson.JSON;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.stmt.BlockStmt;
import com.github.javaparser.ast.stmt.Statement;
import com.github.javaparser.ast.type.ClassOrInterfaceType;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.summarizer.pojo.JBlock;
import com.summarizer.pojo.JClass;
import com.summarizer.pojo.JMethod;
import com.summarizer.pojo.JPackage;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileWriter;
import java.util.ArrayList;
import java.util.List;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(name = "JavaCodeParser", mixinStandardHelpOptions = true, version = "JavaCodeParser 1.0")
public class JavaCodeParser implements Runnable {
    private static final Integer MAX_BLOCK_LENGTH = 512;

    @Option(names = {"-r", "--repo-dir"}, description = "Path to the directory of repository", required = true)
    private String repoDirPath;

    @Option(names = {"-o", "--output"}, description = "Path to the output file")
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
            if (file.isDirectory()) {
                subPackages.add(extractPackage(file));
            } else {
                if (file.getName().endsWith(".java")) {
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
                        String implTypes = "";
                        for (ClassOrInterfaceType t : coi.getImplementedTypes()) implTypes += t + ", ";
                        if (implTypes.length() > 0) implTypes = implTypes.substring(0, implTypes.length() - 2);

                        // 拼接继承类
                        String extendsTypes = "";
                        for (ClassOrInterfaceType t : coi.getExtendedTypes()) extendsTypes += t + ", ";
                        if (extendsTypes.length() > 0) extendsTypes = extendsTypes.substring(0, extendsTypes.length() - 2);

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
                        String implTypes = "";
                        for (ClassOrInterfaceType t : e.getImplementedTypes()) implTypes += t + ", ";
                        if (implTypes.length() > 0) implTypes = implTypes.substring(0, implTypes.length() - 2);

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
    public static List<JMethod> extractMethods(TypeDeclaration cu) {
        ArrayList<JMethod> methods = new ArrayList<>();

        cu.findAll(MethodDeclaration.class).forEach(md -> {
            // 忽略空方法 / 构造器 / toString / hashCode / equals / getter / setter 方法
            if (md.getBody().isEmpty() ||
                    md.isConstructorDeclaration() ||
                    md.getNameAsString().equals("toString") ||
                    md.getNameAsString().equals("hashCode") ||
                    md.getNameAsString().equals("equals") ||
                    md.getNameAsString().startsWith("get") ||
                    md.getNameAsString().startsWith("set")) {
                return;
            }

            // 获取方法签名
            String params = "";
            for (Parameter p : md.getParameters()) params += p.getType() + " " + p.getName() + ", ";
            if (params.length() > 0) params = params.substring(0, params.length() - 2);
            String signature = md.getType() + " " + md.getName() + "(" + params + ")";

            JBlock jBlock;
            BlockStmt body = md.getBody().get();
            if(signature.length() + body.toString().length() > MAX_BLOCK_LENGTH) {
                jBlock = splitBlock(body);
            } else {
                jBlock = new JBlock(formatBlock(body.toString()), new ArrayList<>());
            }

            methods.add(new JMethod(
                    signature,
                    jBlock.getContent(),
                    jBlock.getBlocks()
            ));
        });

        return methods;
    }

    /**
     * 将一个代码块分割为多个长度不超过 MAX_BLOCK_LENGTH 的代码块
     */
    public static JBlock splitBlock(Statement body) {
        String content = formatBlock(body.toString());
        ArrayList<JBlock> jBlocks = new ArrayList<>();

        for (Statement stmt : body.findAll(Statement.class, s -> s.getParentNode().get() == body)) {
            String blockContent = formatBlock(stmt.toString());
            if (blockContent.length() > MAX_BLOCK_LENGTH * 0.75) {
                jBlocks.add(splitBlock(stmt));

                // 将原代码块中的内容替换为占位符
                content = content.replace(blockContent, "<BLOCK>");
            }
        }

        // 待改！！！
        // 若分割完后仍然超过 MAX_BLOCK_LENGTH，则截断
        if (content.length() > MAX_BLOCK_LENGTH) {
            System.out.println("cut off from: \n" + content + "\n" + "to: \n" + content.substring(0, MAX_BLOCK_LENGTH));
            content = content.substring(0, MAX_BLOCK_LENGTH);
        }

        return new JBlock(content, jBlocks);
    }

    public static String formatBlock(String block) {
        return block.replaceAll("\n", " ")
                .replaceAll(" +", " ");
    }
}