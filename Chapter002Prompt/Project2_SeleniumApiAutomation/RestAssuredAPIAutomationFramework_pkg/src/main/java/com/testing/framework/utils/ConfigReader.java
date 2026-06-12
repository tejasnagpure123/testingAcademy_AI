package com.testing.framework.utils;

import java.io.FileInputStream;
import java.io.InputStream;
import java.util.Properties;

public final class ConfigReader {
    private static final Properties properties = new Properties();

    static {
        try {
            String env = System.getProperty("env");
            if (env == null || env.isEmpty()) {
                env = "qa";
            }

            try (InputStream in = new FileInputStream("src/test/resources/config.properties")) {
                properties.load(in);
            }

            String envFile = String.format("src/test/resources/%s.properties", env);
            try (InputStream ein = new FileInputStream(envFile)) {
                Properties envProps = new Properties();
                envProps.load(ein);
                properties.putAll(envProps);
            } catch (Exception e) {
                // env file optional
            }
        } catch (Exception e) {
            throw new RuntimeException("Failed to load configuration", e);
        }
    }

    private ConfigReader() {}

    public static String get(String key) {
        return properties.getProperty(key);
    }

    public static int getInt(String key, int defaultValue) {
        String v = properties.getProperty(key);
        if (v == null) return defaultValue;
        return Integer.parseInt(v);
    }
}
