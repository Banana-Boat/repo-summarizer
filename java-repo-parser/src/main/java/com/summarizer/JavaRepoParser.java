package com.summarizer;

import ai.djl.huggingface.tokenizers.HuggingFaceTokenizer;
import com.github.javaparser.StaticJavaParser;
import com.github.javaparser.ast.CompilationUnit;
import com.github.javaparser.ast.body.ClassOrInterfaceDeclaration;
import com.github.javaparser.ast.body.EnumDeclaration;
import com.github.javaparser.ast.body.MethodDeclaration;
import com.github.javaparser.ast.body.TypeDeclaration;
import com.github.javaparser.ast.stmt.BlockStmt;
import com.github.javaparser.ast.stmt.Statement;
import com.github.javaparser.ast.stmt.SwitchEntry;
import com.github.javaparser.ast.visitor.VoidVisitorAdapter;
import com.summarizer.pojo.*;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.IOException;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;

public class JavaRepoParser {
    private static final String BLOCK_PLACEHOLDER = "<BLOCK>";
    private Tokenizer tokenizer;
    private Integer nodeCount = 0; // 总节点数
    private Integer blockCount = 0; // 分割的代码片段数
    private Integer cutCount = 0; // 截断的代码片段数
    private Integer totalCutCharCount = 0; // 总截断的字符数
    public List<String> logs = new ArrayList<>(); // 截断日志

    public JavaRepoParser(Tokenizer tokenizer) {
        this.tokenizer = tokenizer;
    }

    public JRepo extractRepo(File dir) throws Exception {
        if (!dir.isDirectory())
            throw new IllegalArgumentException("param is not a directory");

        JPackage jPackage = extractPackage(dir, dir.getName());

        logs.add(0,
                "分割代码片段数：" + blockCount + "\n截断代码片段数：" + cutCount +
                        "\n不完整节点率：" + (double) cutCount / nodeCount +
                        "\n平均截断token数：" + (double) totalCutCharCount / cutCount);

        return new JRepo(
                jPackage,
                nodeCount
        );
    }

    /**
     * 提取一个目录中的所有子包 / 类 / 接口 / 枚举
     */
    public JPackage extractPackage(File dir, String pkgName) throws Exception {
        if (!dir.isDirectory())
            throw new IllegalArgumentException("param is not a directory");

        ArrayList<JPackage> subPackages = new ArrayList<>();
        ArrayList<JClass> classes = new ArrayList<>();

        // 处理当前目录下只有一个子目录的情况：合并目录名，只产生一个节点
        File[] subFiles = Objects.requireNonNull(dir.listFiles());
        if (subFiles.length == 1 && subFiles[0].isDirectory()) {
            return extractPackage(subFiles[0], pkgName + "." + subFiles[0].getName());
        }

        for (File file : subFiles) {
            if (file.isDirectory()) {
                subPackages.add(extractPackage(file, file.getName()));
            } else {
                if (file.getName().endsWith(".java")) {
                    classes.addAll(extractClasses(file));
                }
            }
        }

        nodeCount++;
        return new JPackage(
                pkgName,
                dir.getPath(),
                classes,
                subPackages
        );
    }

    /**
     * 提取一个文件中的所有类 / 接口 / 枚举
     */
    public List<JClass> extractClasses(File file) throws FileNotFoundException {
        ArrayList<JClass> classes = new ArrayList<>();

            CompilationUnit cu = StaticJavaParser.parse(file);
            cu.accept(new VoidVisitorAdapter<Void>() {
                @Override
                public void visit(CompilationUnit cu, Void arg) {
                    super.visit(cu, arg);
                    // 获取顶层的类 / 接口中的所有方法
                    for (ClassOrInterfaceDeclaration coi : cu.findAll(ClassOrInterfaceDeclaration.class)) {
                        // 拼接签名
                        String signature = (coi.isAbstract() ? "abstract " : "") +
                                (coi.isInterface() ? "interface " : "class ") + coi.getNameAsString() +
                                ((coi.getExtendedTypes().size() == 0) ? "" :
                                        " extends " + coi.getExtendedTypes().toString()
                                                .replace("[", "").replace("]", "")) +
                                ((coi.getImplementedTypes().size() == 0) ? "" :
                                        " implements " + coi.getImplementedTypes().toString()
                                                .replace("[", "").replace("]", ""));

                        nodeCount++;
                        classes.add(new JClass(
                                coi.getNameAsString(),
                                signature,
                                extractMethods(coi, file.getPath()),
                                file.getPath()
                        ));
                    }

                    // 获取枚举类中的所有方法
                    for (EnumDeclaration e : cu.findAll(EnumDeclaration.class)) {
                        // 拼接签名
                        String signature = "enum " + e.getNameAsString() +
                                ((e.getImplementedTypes().size() == 0) ? "" :
                                        " implements " + e.getImplementedTypes().toString()
                                                .replace("[", "").replace("]", ""));

                        nodeCount++;
                        classes.add(new JClass(
                                e.getNameAsString(),
                                signature,
                                extractMethods(e, file.getPath()),
                                file.getPath()
                        ));
                    }
                }
            }, null);


        return classes;
    }

    /**
     * 提取一个类 / 接口 / 枚举中的所有方法
     */
    public List<JMethod> extractMethods(TypeDeclaration cu, String filePath) {
        ArrayList<JMethod> methods = new ArrayList<>();

        for (MethodDeclaration md : cu.findAll(MethodDeclaration.class)) {
            // 忽略空方法 / 构造器 / toString / hashCode / equals / getter / setter 方法
            if (md.getBody().isEmpty() ||
                    md.isConstructorDeclaration() ||
                    md.getNameAsString().equals("toString") ||
                    md.getNameAsString().equals("hashCode") ||
                    md.getNameAsString().equals("equals") ||
                    md.getNameAsString().startsWith("get") ||
                    md.getNameAsString().startsWith("set")) {
                break;
            }

            String signature = md.getType() + " " + md.getName() +
                    md.getParameters().toString().replace("[", "(").replace("]", ")");

            JCodeSnippet jCodeSnippet;
            BlockStmt body = md.getBody().get();
            if (!tokenizer.isLegalSource(signature + body)) {
                // 继续分裂用jCodeSnippet替代method节点，jCodeSnippet中nodeCount已经加过
                jCodeSnippet = splitCodeSnippet(body, formatBlock(body.toString()), filePath);
            } else {
                nodeCount++; // 直接算作一个method节点
                jCodeSnippet = new JCodeSnippet(formatBlock(body.toString()), new ArrayList<>());
            }

            methods.add(new JMethod(
                    signature,
                    jCodeSnippet.getContent(),
                    jCodeSnippet.getCodeSnippets()
            ));
        }

        return methods;
    }

    /**
     * 将一个代码片段分割为多个长度不超过 MAX_LLM_LENGTH 的代码片段
     * TODO： 无法处理多个较短的语句构成的代码片段
     *
     * @param body    待处理的语句节点
     * @param content 该语句节点（可以为其父节点）的字符串内容（未替换占位符）
     */
    public JCodeSnippet splitCodeSnippet(Statement body, String content, String filePath) {
        ArrayList<JCodeSnippet> jCodeSnippets = new ArrayList<>();

        for (Statement stmt : body.findAll(Statement.class, s -> s.getParentNode().get() == body)) {
            String blockContent = formatBlock(stmt.toString());

            if (!tokenizer.isLegalCodeSnippet(blockContent)) {
                switch (stmt.getClass().getSimpleName()) {
                    case "IfStmt":
                        Statement thenStmt = stmt.asIfStmt().getThenStmt();
                        String ifBlockContent = "if (" + stmt.asIfStmt().getCondition() + ") " + formatBlock(thenStmt.toString());

                        if (stmt.asIfStmt().getElseStmt().isPresent()) { // 若有else-if / else则递归处理
                            Statement elseStmt = stmt.asIfStmt().getElseStmt().get();
                            String elseBlockContent = "else " + formatBlock(elseStmt.toString());

                            // 判断若then中内容替换后，if-else整体是否超过上限（因为存在递归关系）
                            if (!tokenizer.isLegalCodeSnippet(replaceOnce(content, ifBlockContent, BLOCK_PLACEHOLDER))) {
                                // 若仍然超过则分别对then和else进行分割，并替换为两个占位符
                                jCodeSnippets.add(splitCodeSnippet(thenStmt, ifBlockContent, filePath));
                                jCodeSnippets.add(splitCodeSnippet(elseStmt, elseBlockContent, filePath));
                                content = replaceOnce(content, ifBlockContent, BLOCK_PLACEHOLDER);
                                content = replaceOnce(content, elseBlockContent, BLOCK_PLACEHOLDER);
                            } else {
                                // 若未超过则只对then进行分割，并替换为一个占位符
                                String tempContent = ifBlockContent + " " + elseBlockContent;
                                jCodeSnippets.add(splitCodeSnippet(thenStmt, tempContent, filePath));
                                content = replaceOnce(content, tempContent, BLOCK_PLACEHOLDER);
                            }
                        } else { // 若无else-if / else
                            jCodeSnippets.add(splitCodeSnippet(thenStmt, ifBlockContent, filePath));
                            content = replaceOnce(content, ifBlockContent, BLOCK_PLACEHOLDER);
                        }
                        break;
                    case "SwitchStmt":
                        for (SwitchEntry entry : stmt.asSwitchStmt().getEntries()) {
                            for (Statement statement : entry.getStatements()) {
                                String statementContent = formatBlock(statement.toString());
                                // 若当前statement超过上限，则分割
                                if (!tokenizer.isLegalCodeSnippet(statementContent)) {
                                    jCodeSnippets.add(splitCodeSnippet(statement, statementContent, filePath));
                                    content = replaceOnce(content, statementContent, BLOCK_PLACEHOLDER);
                                }
                            }
                        }
                        break;
                    case "TryStmt":
                        jCodeSnippets.add(splitCodeSnippet(stmt.asTryStmt().getTryBlock(), blockContent, filePath));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        // 不对catch和finally进行分割，若超过则直接截断
                        break;
                    case "ForStmt":
                        jCodeSnippets.add(splitCodeSnippet(stmt.asForStmt().getBody(), blockContent, filePath));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "WhileStmt":
                        jCodeSnippets.add(splitCodeSnippet(stmt.asWhileStmt().getBody(), blockContent, filePath));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "DoStmt":
                        jCodeSnippets.add(splitCodeSnippet(stmt.asDoStmt().getBody(), blockContent, filePath));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "ForEachStmt":
                        jCodeSnippets.add(splitCodeSnippet(stmt.asForEachStmt().getBody(), blockContent, filePath));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    case "SynchronizedStmt":
                        jCodeSnippets.add(splitCodeSnippet(stmt.asSynchronizedStmt().getBody(), blockContent, filePath));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                        break;
                    default:
                        logs.add(filePath + "\n" + stmt.getRange().get() + "\n" +
                                "Unhandled long statement type: " + stmt.getClass().getSimpleName());
                        jCodeSnippets.add(splitCodeSnippet(stmt, blockContent, filePath));
                        content = replaceOnce(content, blockContent, BLOCK_PLACEHOLDER);
                }
            }
        }

        // 若分割完后仍然超过 MAX_LLM_LENGTH，则截断
        if (!tokenizer.isLegalSource(content)) {
            totalCutCharCount += tokenizer.getTokenNum(content) - tokenizer.getMaxSourceLength();
            cutCount++;

            String cutContent = tokenizer.cutToLegalSource(content);

            // 记录日志信息
            logs.add(filePath + "\n" + body.getRange().get() + "\n" +
                    "cut off from: \n" + content + "\n" +
                    "to: \n" + cutContent);

            content = cutContent;
        }

        blockCount++;
        nodeCount++;
        return new JCodeSnippet(content, jCodeSnippets);
    }

    // 替换第一个匹配的字符串。String自带的方法第一个参数为正则表达式，而待替换的代码片段存在存在正则中的特殊字符，故自己实现
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