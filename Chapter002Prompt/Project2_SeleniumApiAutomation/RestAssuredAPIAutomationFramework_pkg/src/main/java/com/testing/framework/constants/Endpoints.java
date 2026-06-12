package com.testing.framework.constants;

public final class Endpoints {
    private Endpoints() {}

    public static final String CREATE_USER = "/api/users";
    public static final String GET_USER = "/api/users/{id}";
    public static final String UPDATE_USER = "/api/users/{id}";
    public static final String DELETE_USER = "/api/users/{id}";

    public static final String AUTH_TOKEN = "/api/auth/token";
}
