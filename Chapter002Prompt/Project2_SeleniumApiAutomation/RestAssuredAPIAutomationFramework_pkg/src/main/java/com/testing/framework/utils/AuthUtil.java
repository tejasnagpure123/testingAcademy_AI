package com.testing.framework.utils;

import java.util.concurrent.atomic.AtomicReference;

public final class AuthUtil {
    private static final AtomicReference<String> bearerToken = new AtomicReference<>();

    private AuthUtil() {}

    public static void setBearerToken(String token) {
        bearerToken.set(token);
    }

    public static String getBearerToken() {
        return bearerToken.get();
    }

    public static String buildBasicAuthHeader(String username, String password) {
        String creds = username + ":" + password;
        return "Basic " + java.util.Base64.getEncoder().encodeToString(creds.getBytes());
    }
}
