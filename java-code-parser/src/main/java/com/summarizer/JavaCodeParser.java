package com.summarizer;

import com.alibaba.fastjson.JSON;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.*;
import com.github.javaparser.ast.stmt.*;
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
import java.util.Objects;

import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

@Command(name = "JavaCodeParser", mixinStandardHelpOptions = true, version = "JavaCodeParser 1.0")
public class JavaCodeParser implements Runnable {
    private static final Integer MAX_LLM_LENGTH = 512;
    private static final Double MAX_BLOCK_LENGTH = MAX_LLM_LENGTH * 0.75;
    private static final String BLOCK_PLACEHOLDER = "<BLOCK>";

    @Option(names = {"-r", "--repo-dir"}, description = "Path to the directory of repository", required = true)
    private String repoDirPath = "";

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
    public JPackage extractPackage(File dir) {
        if (!dir.isDirectory()) return null;

        ArrayList<JPackage> subPackages = new ArrayList<>();
        ArrayList<JClass> classes = new ArrayList<>();

        for (File file : Objects.requireNonNull(dir.listFiles())) {
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
    public List<JClass> extractClasses(File file) {
        ArrayList<JClass> classes = new ArrayList<>();

        try {
            CompilationUnit cu = StaticJavaParser.parse(file);
            cu.accept(new VoidVisitorAdapter<Void>() {
                @Override
                public void visit(CompilationUnit cu, Void arg) {
                    super.visit(cu, arg);
                    // 获取顶层的类 / 接口中的所有方法
                    cu.findAll(ClassOrInterfaceDeclaration.class).forEach(coi -> {
                        // 拼接签名
                        String signature = (coi.isAbstract() ? "abstract " : "") +
                                (coi.isInterface() ? "interface " : "class ") + coi.getNameAsString() +
                                ((coi.getExtendedTypes().size() == 0) ? "" :
                                        " extends " + coi.getExtendedTypes().toString().replace("[", "").replace("]", "")) +
                                ((coi.getImplementedTypes().size() == 0) ? "" :
                                        " implements " + coi.getImplementedTypes().toString().replace("[", "").replace("]", ""));

                        classes.add(new JClass(
                                coi.getNameAsString(),
                                signature,
                                extractMethods(coi),
                                file.getPath()
                        ));
                    });

                    // 获取枚举类中的所有方法
                    cu.findAll(EnumDeclaration.class).forEach(e -> {
                        // 拼接签名
                        String signature = "enum " + e.getNameAsString() +
                                ((e.getImplementedTypes().size() == 0) ? "" :
                                        " implements " + e.getImplementedTypes().toString().replace("[", "").replace("]", ""));

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
    public List<JMethod> extractMethods(TypeDeclaration cu) {
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

            String signature = md.getType() + " " + md.getName() + md.getParameters().toString().replace("[", "(").replace("]", ")");

            JBlock jBlock;
            BlockStmt body = md.getBody().get();
            if (signature.length() + body.toString().length() > MAX_LLM_LENGTH) {
                jBlock = splitBlock(body, formatBlock(body.toString()));
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
     * 将一个代码块分割为多个长度不超过 MAX_LLM_LENGTH 的代码块
     * TODO： 无法处理多个单行的语句构成的代码块
     *
     * @param body    待处理的语句节点
     * @param content 该语句节点（可以为其父节点）的字符串内容（未替换占位符）
     */
    public JBlock splitBlock(Statement body, String content) {
        ArrayList<JBlock> jBlocks = new ArrayList<>();

        for (Statement stmt : body.findAll(Statement.class, s -> s.getParentNode().get() == body)) {
            String blockContent = formatBlock(stmt.toString());

            if (blockContent.length() > MAX_BLOCK_LENGTH) {
                switch (stmt.getClass().getSimpleName()) {
                    case "IfStmt":
                        Statement thenStmt = stmt.asIfStmt().getThenStmt();
                        String ifBlockContent = "if (" + stmt.asIfStmt().getCondition() + ") " + formatBlock(thenStmt.toString());

                        if (stmt.asIfStmt().getElseStmt().isPresent()) { // 若有else-if / else则递归处理
                            Statement elseStmt = stmt.asIfStmt().getElseStmt().get();
                            String elseBlockContent = "else " + formatBlock(elseStmt.toString());

                            // 判断若then中内容替换后，if-else整体是否超过上限（因为存在递归关系）
                            if (replaceOnce(content, ifBlockContent, BLOCK_PLACEHOLDER).length() > MAX_BLOCK_LENGTH) { // 若仍然超过则分别对then和else进行分割，并替换为两个占位符
                                jBlocks.add(splitBlock(thenStmt, ifBlockContent));
                                jBlocks.add(splitBlock(elseStmt, elseBlockContent));
                                content = replaceOnce(content, ifBlockContent, BLOCK_PLACEHOLDER)
                                        .replaceFirst(elseBlockContent, BLOCK_PLACEHOLDER);
                            } else { // 若未超过则只对then进行分割，并替换为一个占位符
                                String tempContent = ifBlockContent + " " + elseBlockContent;
                                jBlocks.add(splitBlock(thenStmt, tempContent));
                                content = replaceOnce(content, tempContent, BLOCK_PLACEHOLDER);
                            }
                        } else { // 若无else-if / else
                            jBlocks.add(splitBlock(thenStmt, ifBlockContent));
                            content = replaceOnce(content, ifBlockContent, BLOCK_PLACEHOLDER);
                        }
                        break;
                    case "SwitchStmt":
                        for (SwitchEntry entry : stmt.asSwitchStmt().getEntries()) {
                            for (Statement statement : entry.getStatements()) {
                                String statementContent = formatBlock(statement.toString());
                                // 若当前statement超过上限，则分割
                                if (statementContent.length() > MAX_BLOCK_LENGTH) {
                                    jBlocks.add(splitBlock(statement, statementContent));
                                    content = replaceOnce(content, statementContent, BLOCK_PLACEHOLDER);
                                }
                            }
                        }
                        break;
                    case "TryStmt":
                        jBlocks.add(splitBlock(stmt.asTryStmt().getTryBlock(), blockContent));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        // 不对catch和finally进行分割，若超过则直接截断
                        break;
                    case "ForStmt":
                        jBlocks.add(splitBlock(stmt.asForStmt().getBody(), blockContent));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "WhileStmt":
                        jBlocks.add(splitBlock(stmt.asWhileStmt().getBody(), blockContent));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "DoStmt":
                        jBlocks.add(splitBlock(stmt.asDoStmt().getBody(), blockContent));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "ForEachStmt":
                        jBlocks.add(splitBlock(stmt.asForEachStmt().getBody(), blockContent));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "SynchronizedStmt":
                        jBlocks.add(splitBlock(stmt.asSynchronizedStmt().getBody(), blockContent));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    default:
                        System.out.println("Unhandled long statement type: " + stmt.getClass().getSimpleName());
                        jBlocks.add(splitBlock(stmt, blockContent));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                }
            }
        }

        // 若分割完后仍然超过 MAX_LLM_LENGTH，则截断
        if (content.length() > MAX_LLM_LENGTH) {
            System.out.println("cut off from: \n" + content + "\n" + "to: \n" + content.substring(0, MAX_LLM_LENGTH));
            content = content.substring(0, MAX_LLM_LENGTH);
        }

        return new JBlock(content, jBlocks);
    }

    // 替换第一个匹配的字符串。String自带的方法第一个参数为正则表达式，而待替换的代码块存在存在正则中的特殊字符，故自己实现
    public String replaceOnce(String str, String target, String replacement) {
        int idx = str.indexOf(target);
        if (idx == -1) {
            return str;
        } else {
            return str.substring(0, idx) + replacement + str.substring(idx + target.length());
        }
    }

    public String formatBlock(String block) {
        return block.replaceAll("\n", " ")
                .replaceAll(" +", " ");
    }
}