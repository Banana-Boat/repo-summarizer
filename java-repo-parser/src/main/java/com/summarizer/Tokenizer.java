package com.summarizer;

import ai.djl.huggingface.tokenizers.HuggingFaceTokenizer;

import java.io.IOException;
import java.nio.file.Paths;
import java.util.Arrays;

public class Tokenizer {
    private Integer MAX_SOURCE_LENGTH;
    private Double MAX_CODE_SNIPPET_LENGTH;
    private HuggingFaceTokenizer tokenizer;

    public Tokenizer(String path, Integer maxSourceLength) throws IOException {
        tokenizer = HuggingFaceTokenizer.newInstance(Paths.get(path));
        MAX_SOURCE_LENGTH = maxSourceLength;
        MAX_CODE_SNIPPET_LENGTH = maxSourceLength * 0.5;
    }

    public Integer getMaxSourceLength() {
        return MAX_SOURCE_LENGTH;
    }

    public Double getMaxCodeSnippetLength() {
        return MAX_CODE_SNIPPET_LENGTH;
    }
    public Boolean isLegalCodeSnippet(String code) {
        return tokenizer.tokenize(code).size() <= MAX_CODE_SNIPPET_LENGTH;
    }

    public Boolean isLegalSource(String source) {
        return tokenizer.tokenize(source).size() <= MAX_SOURCE_LENGTH;
    }

    public Integer getTokenNum(String source) {
        return tokenizer.tokenize(source).size();
    }

    public String cutToLegalSource(String source) {
        if (tokenizer.tokenize(source).size() <= MAX_SOURCE_LENGTH) {
            return source;
        }

        long[] ids = tokenizer.encode(source).getIds();
        long[] cutIds = Arrays.copyOfRange(ids, 0, MAX_SOURCE_LENGTH);

        return tokenizer.decode(cutIds, true);
    }

}
