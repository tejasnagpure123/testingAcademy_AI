package com.testing.framework.utils;

import io.restassured.builder.RequestSpecBuilder;
import io.restassured.specification.RequestSpecification;
import io.restassured.filter.log.RequestLoggingFilter;
import io.restassured.filter.log.ResponseLoggingFilter;

public final class RequestSpecBuilderUtil {
    private static RequestSpecification requestSpec;

    private RequestSpecBuilderUtil() {}

    public static RequestSpecification getRequestSpec() {
        if (requestSpec == null) {
            RequestSpecBuilder builder = new RequestSpecBuilder();
            String baseUri = ConfigReader.get("base.uri");
            builder.setBaseUri(baseUri);
            String basePath = ConfigReader.get("base.path");
            if (basePath != null) builder.setBasePath(basePath);
            builder.addHeader("Accept", "application/json");
            builder.addHeader("Content-Type", "application/json");
            String token = AuthUtil.getBearerToken();
            if (token != null) builder.addHeader("Authorization", "Bearer " + token);
            builder.setRelaxedHTTPSValidation();
            builder.addFilter(new RequestLoggingFilter());
            builder.addFilter(new ResponseLoggingFilter());
            requestSpec = builder.build();
        }
        return requestSpec;
    }

    public static void reset() {
        requestSpec = null;
    }
}
