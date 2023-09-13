package com.summarizer;

import com.alibaba.fastjson.JSON;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Option;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;

@Command(name = "JavaRepoParser", mixinStandardHelpOptions = true, version = "JavaRepoParser 1.0")
public class Main implements Runnable {
    @Option(names = {"-r", "--repo-path"}, description = "Path to the directory of repository", required = true)
    private String repoPath = "";
    @Option(names = {"-t", "--tokenizer-path"}, description = "Path to the tokenizer configuration file", required = true)
    private String tokenizerPath = "";
    @Option(names = {"-m", "--max-source-length"}, description = "Max length of input source code sending to llm")
    private Integer maxSourceLength = 512;
    @Option(names = {"-o", "--output-path"}, description = "Path to the output file")
    private String outputPath = "./parse_output.json";
    @Option(names = {"-l", "--log-path"}, description = "Path to the log file")
    private String logPath = "./parse_log.txt";

    public static void main(String[] args) {
        int exitCode = new CommandLine(new Main()).execute(args);
        System.exit(exitCode);
    }

    @Override
    public void run() {
        Logger logger = LoggerFactory.getLogger(Main.class);

        File dir = new File(repoPath);
        if (!dir.isDirectory()) {
            logger.error("JavaRepoParser: " + repoPath + " is not a directory");
            System.exit(1);
        }

        Tokenizer tokenizer = null;
        try {
            tokenizer = new Tokenizer(tokenizerPath, maxSourceLength);
        } catch (IOException e) {
            e.printStackTrace();
            System.exit(1);
        }

        JavaRepoParser parser = new JavaRepoParser(tokenizer);

        // 写入解析结果
        String json = JSON.toJSONString(parser.extractRepo(dir));
        try (FileWriter fw = new FileWriter(outputPath)) {
            fw.write(json);
            logger.info("JavaRepoParser: Result file was written to " + outputPath);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }


        // 写入日志信息
        try (FileWriter fw = new FileWriter(logPath)) {
            for (String log : parser.logs) {
                fw.write(log + "\n==================================================================\n");
            }
            logger.info("JavaRepoParser: Log file was written to " + logPath);
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }

}